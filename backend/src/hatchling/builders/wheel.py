from __future__ import annotations

import csv
import hashlib
import os
import stat
import tempfile
import zipfile
from io import StringIO

from hatchling.__about__ import __version__
from hatchling.builders.config import BuilderConfig
from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.builders.utils import (
    format_file_hash,
    get_known_python_major_versions,
    get_reproducible_timestamp,
    normalize_archive_path,
    normalize_file_permissions,
    normalize_inclusion_map,
    replace_file,
    set_zip_info_mode,
)
from hatchling.metadata.spec import DEFAULT_METADATA_VERSION, get_core_metadata_constructors

EDITABLES_MINIMUM_VERSION = '0.3'


class RecordFile:
    def __init__(self):
        self.__file_obj = StringIO()
        self.__writer = csv.writer(self.__file_obj, delimiter=',', quotechar='"', lineterminator='\n')

    def write(self, record: tuple[str, str, str]) -> None:
        self.__writer.writerow(record)

    def construct(self) -> str:
        return self.__file_obj.getvalue()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__file_obj.close()


class WheelArchive:
    def __init__(self, project_id, reproducible):
        """
        https://peps.python.org/pep-0427/#abstract
        """
        self.metadata_directory = f'{project_id}.dist-info'
        self.shared_data_directory = f'{project_id}.data'

        self.reproducible = reproducible
        if self.reproducible:
            self.time_tuple = self.get_reproducible_time_tuple()
        else:
            self.time_tuple = None

        raw_fd, self.path = tempfile.mkstemp(suffix='.whl')
        self.fd = os.fdopen(raw_fd, 'w+b')
        self.zf = zipfile.ZipFile(self.fd, 'w', compression=zipfile.ZIP_DEFLATED)

    @staticmethod
    def get_reproducible_time_tuple():
        from datetime import datetime, timezone

        d = datetime.fromtimestamp(get_reproducible_timestamp(), timezone.utc)
        return d.year, d.month, d.day, d.hour, d.minute, d.second

    def add_file(self, included_file):
        relative_path = normalize_archive_path(included_file.distribution_path)
        file_stat = os.stat(included_file.path)

        if self.reproducible:
            zip_info = zipfile.ZipInfo(relative_path, self.time_tuple)

            # https://github.com/takluyver/flit/pull/66
            new_mode = normalize_file_permissions(file_stat.st_mode)
            set_zip_info_mode(zip_info, new_mode & 0xFFFF)
            if stat.S_ISDIR(file_stat.st_mode):  # no cov
                zip_info.external_attr |= 0x10
        else:
            zip_info = zipfile.ZipInfo.from_file(included_file.path, relative_path)

        zip_info.compress_type = zipfile.ZIP_DEFLATED

        hash_obj = hashlib.sha256()
        with open(included_file.path, 'rb') as in_file, self.zf.open(zip_info, 'w') as out_file:
            while True:
                chunk = in_file.read(16384)
                if not chunk:
                    break

                hash_obj.update(chunk)
                out_file.write(chunk)

        hash_digest = format_file_hash(hash_obj.digest())
        return relative_path, f'sha256={hash_digest}', str(file_stat.st_size)

    def write_metadata(self, relative_path, contents):
        relative_path = f'{self.metadata_directory}/{normalize_archive_path(relative_path)}'
        return self.write_file(relative_path, contents)

    def add_shared_file(self, shared_file):
        shared_file.distribution_path = f'{self.shared_data_directory}/data/{shared_file.distribution_path}'
        return self.add_file(shared_file)

    def add_extra_metadata_file(self, extra_metadata_file):
        extra_metadata_file.distribution_path = (
            f'{self.metadata_directory}/extra_metadata/{extra_metadata_file.distribution_path}'
        )
        return self.add_file(extra_metadata_file)

    def write_file(self, relative_path, contents):
        if not isinstance(contents, bytes):
            contents = contents.encode('utf-8')

        time_tuple = self.time_tuple or (2020, 2, 2, 0, 0, 0)
        zip_info = zipfile.ZipInfo(relative_path, time_tuple)
        set_zip_info_mode(zip_info)

        hash_obj = hashlib.sha256(contents)
        hash_digest = format_file_hash(hash_obj.digest())
        self.zf.writestr(zip_info, contents, compress_type=zipfile.ZIP_DEFLATED)

        return relative_path, f'sha256={hash_digest}', str(len(contents))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.zf.close()
        self.fd.close()


class WheelBuilderConfig(BuilderConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__include_defined = bool(
            self.target_config.get('include', self.build_config.get('include'))
            or self.target_config.get('packages', self.build_config.get('packages'))
            or self.target_config.get('only-include', self.build_config.get('only-include'))
        )
        self.__include = []
        self.__exclude = []
        self.__packages = []
        self.__only_include = []

        self.__core_metadata_constructor = None
        self.__shared_data = None
        self.__extra_metadata = None
        self.__strict_naming = None

    def set_default_file_selection(self):
        if self.__include or self.__exclude or self.__packages or self.__only_include:
            return

        for project_name in (
            self.builder.normalize_file_name_component(self.builder.metadata.core.raw_name),
            self.builder.normalize_file_name_component(self.builder.metadata.core.name),
        ):
            if os.path.isfile(os.path.join(self.root, project_name, '__init__.py')):
                self.__packages.append(project_name)
                break
            elif os.path.isfile(os.path.join(self.root, 'src', project_name, '__init__.py')):
                self.__packages.append(f'src/{project_name}')
                break
            elif os.path.isfile(os.path.join(self.root, f'{project_name}.py')):
                self.__only_include.append(f'{project_name}.py')
                break
            else:
                from glob import glob

                possible_namespace_packages = glob(os.path.join(self.root, '*', project_name, '__init__.py'))
                if len(possible_namespace_packages) == 1:
                    relative_path = os.path.relpath(possible_namespace_packages[0], self.root)
                    namespace = relative_path.split(os.sep)[0]
                    self.__packages.append(namespace)
                    break
        else:
            self.__include.append('*.py')
            self.__exclude.append('test*')

    def default_include(self):
        if not self.__include_defined:
            self.set_default_file_selection()

        return self.__include

    def default_exclude(self):
        if not self.__include_defined:
            self.set_default_file_selection()

        return self.__exclude

    def default_packages(self):
        if not self.__include_defined:
            self.set_default_file_selection()

        return self.__packages

    def default_only_include(self):
        if not self.__include_defined:
            self.set_default_file_selection()

        return self.__only_include

    @property
    def core_metadata_constructor(self):
        if self.__core_metadata_constructor is None:
            core_metadata_version = self.target_config.get('core-metadata-version', DEFAULT_METADATA_VERSION)
            if not isinstance(core_metadata_version, str):
                raise TypeError(
                    f'Field `tool.hatch.build.targets.{self.plugin_name}.core-metadata-version` must be a string'
                )

            constructors = get_core_metadata_constructors()
            if core_metadata_version not in constructors:
                raise ValueError(
                    f'Unknown metadata version `{core_metadata_version}` for field '
                    f'`tool.hatch.build.targets.{self.plugin_name}.core-metadata-version`. '
                    f'Available: {", ".join(sorted(constructors))}'
                )

            self.__core_metadata_constructor = constructors[core_metadata_version]

        return self.__core_metadata_constructor

    @property
    def shared_data(self):
        if self.__shared_data is None:
            shared_data = self.target_config.get('shared-data', {})
            if not isinstance(shared_data, dict):
                raise TypeError(f'Field `tool.hatch.build.targets.{self.plugin_name}.shared-data` must be a mapping')

            for i, (source, relative_path) in enumerate(shared_data.items(), 1):
                if not source:
                    raise ValueError(
                        f'Source #{i} in field `tool.hatch.build.targets.{self.plugin_name}.shared-data` '
                        f'cannot be an empty string'
                    )
                elif not isinstance(relative_path, str):
                    raise TypeError(
                        f'Path for source `{source}` in field '
                        f'`tool.hatch.build.targets.{self.plugin_name}.shared-data` must be a string'
                    )
                elif not relative_path:
                    raise ValueError(
                        f'Path for source `{source}` in field '
                        f'`tool.hatch.build.targets.{self.plugin_name}.shared-data` cannot be an empty string'
                    )

            self.__shared_data = normalize_inclusion_map(shared_data, self.root)

        return self.__shared_data

    @property
    def extra_metadata(self):
        if self.__extra_metadata is None:
            extra_metadata = self.target_config.get('extra-metadata', {})
            if not isinstance(extra_metadata, dict):
                raise TypeError(f'Field `tool.hatch.build.targets.{self.plugin_name}.extra-metadata` must be a mapping')

            for i, (source, relative_path) in enumerate(extra_metadata.items(), 1):
                if not source:
                    raise ValueError(
                        f'Source #{i} in field `tool.hatch.build.targets.{self.plugin_name}.extra-metadata` '
                        f'cannot be an empty string'
                    )
                elif not isinstance(relative_path, str):
                    raise TypeError(
                        f'Path for source `{source}` in field '
                        f'`tool.hatch.build.targets.{self.plugin_name}.extra-metadata` must be a string'
                    )
                elif not relative_path:
                    raise ValueError(
                        f'Path for source `{source}` in field '
                        f'`tool.hatch.build.targets.{self.plugin_name}.extra-metadata` cannot be an empty string'
                    )

            self.__extra_metadata = normalize_inclusion_map(extra_metadata, self.root)

        return self.__extra_metadata

    @property
    def strict_naming(self):
        if self.__strict_naming is None:
            if 'strict-naming' in self.target_config:
                strict_naming = self.target_config['strict-naming']
                if not isinstance(strict_naming, bool):
                    raise TypeError(
                        f'Field `tool.hatch.build.targets.{self.plugin_name}.strict-naming` must be a boolean'
                    )
            else:
                strict_naming = self.build_config.get('strict-naming', True)
                if not isinstance(strict_naming, bool):
                    raise TypeError('Field `tool.hatch.build.strict-naming` must be a boolean')

            self.__strict_naming = strict_naming

        return self.__strict_naming


class WheelBuilder(BuilderInterface):
    """
    Build a binary distribution (.whl file)
    """

    PLUGIN_NAME = 'wheel'

    def get_version_api(self):
        return {'standard': self.build_standard, 'editable': self.build_editable}

    def get_default_versions(self):
        return ['standard']

    def clean(self, directory, versions):
        for filename in os.listdir(directory):
            if filename.endswith('.whl'):
                os.remove(os.path.join(directory, filename))

    def build_standard(self, directory, **build_data):
        if 'tag' not in build_data:
            if build_data['infer_tag']:
                from packaging.tags import sys_tags

                best_matching_tag = next(sys_tags())
                tag_parts = (best_matching_tag.interpreter, best_matching_tag.abi, best_matching_tag.platform)
                build_data['tag'] = '-'.join(tag_parts)
            else:
                build_data['tag'] = self.get_default_tag()

        with WheelArchive(self.artifact_project_id, self.config.reproducible) as archive, RecordFile() as records:
            for included_file in self.recurse_included_files():
                record = archive.add_file(included_file)
                records.write(record)

            self.write_data(archive, records, build_data, build_data['dependencies'])

            records.write((f'{archive.metadata_directory}/RECORD', '', ''))
            archive.write_metadata('RECORD', records.construct())

        target = os.path.join(directory, f"{self.artifact_project_id}-{build_data['tag']}.whl")

        replace_file(archive.path, target)
        return target

    def build_editable(self, directory, **build_data):
        if self.config.dev_mode_dirs:
            return self.build_editable_explicit(directory, **build_data)
        else:
            return self.build_editable_detection(directory, **build_data)

    def build_editable_detection(self, directory, **build_data):
        from editables import EditableProject

        build_data['tag'] = self.get_default_tag()

        with WheelArchive(self.artifact_project_id, self.config.reproducible) as archive, RecordFile() as records:
            exposed_packages = {}
            for included_file in self.recurse_project_files():
                if not included_file.path.endswith('.py'):
                    continue

                relative_path = included_file.relative_path
                distribution_path = included_file.distribution_path
                path_parts = relative_path.split(os.sep)

                # Root file
                if len(path_parts) == 1:  # no cov
                    exposed_packages[os.path.splitext(relative_path)[0]] = os.path.join(self.root, relative_path)
                    continue

                # Root package
                root_module = path_parts[0]
                if distribution_path == relative_path:
                    exposed_packages[root_module] = os.path.join(self.root, root_module)
                else:
                    distribution_module = distribution_path.split(os.sep)[0]
                    try:
                        exposed_packages[distribution_module] = os.path.join(
                            self.root,
                            f'{relative_path[:relative_path.index(distribution_path)]}{distribution_module}',
                        )
                    except ValueError:
                        raise ValueError(
                            'Dev mode installations are unsupported when any path rewrite in the `sources` option '
                            'changes a prefix rather than removes it, see: '
                            'https://github.com/pfmoore/editables/issues/20'
                        ) from None

            editable_project = EditableProject(self.metadata.core.name, self.root)

            if self.config.dev_mode_exact:
                for module, relative_path in exposed_packages.items():
                    editable_project.map(module, relative_path)
            else:
                for relative_path in exposed_packages.values():
                    editable_project.add_to_path(os.path.dirname(relative_path))

            for filename, content in sorted(editable_project.files()):
                record = archive.write_file(filename, content)
                records.write(record)

            for included_file in self.recurse_forced_files(self.get_forced_inclusion_map(build_data)):
                record = archive.add_file(included_file)
                records.write(record)

            extra_dependencies = list(build_data['dependencies'])
            for dependency in editable_project.dependencies():
                if dependency == 'editables':
                    dependency += f'~={EDITABLES_MINIMUM_VERSION}'
                else:  # no cov
                    pass

                extra_dependencies.append(dependency)

            self.write_data(archive, records, build_data, extra_dependencies)

            records.write((f'{archive.metadata_directory}/RECORD', '', ''))
            archive.write_metadata('RECORD', records.construct())

        target = os.path.join(directory, f"{self.artifact_project_id}-{build_data['tag']}.whl")

        replace_file(archive.path, target)
        return target

    def build_editable_explicit(self, directory, **build_data):
        build_data['tag'] = self.get_default_tag()

        with WheelArchive(self.artifact_project_id, self.config.reproducible) as archive, RecordFile() as records:
            directories = sorted(
                os.path.normpath(os.path.join(self.root, relative_directory))
                for relative_directory in self.config.dev_mode_dirs
            )

            record = archive.write_file(f"{self.metadata.core.name.replace('-', '_')}.pth", '\n'.join(directories))
            records.write(record)

            for included_file in self.recurse_forced_files(self.get_forced_inclusion_map(build_data)):
                record = archive.add_file(included_file)
                records.write(record)

            self.write_data(archive, records, build_data, build_data['dependencies'])

            records.write((f'{archive.metadata_directory}/RECORD', '', ''))
            archive.write_metadata('RECORD', records.construct())

        target = os.path.join(directory, f"{self.artifact_project_id}-{build_data['tag']}.whl")

        replace_file(archive.path, target)
        return target

    def write_data(self, archive, records, build_data, extra_dependencies):
        self.add_shared_data(archive, records)

        # Ensure metadata is written last, see https://peps.python.org/pep-0427/#recommended-archiver-features
        self.write_metadata(archive, records, build_data, extra_dependencies=extra_dependencies)

    def add_shared_data(self, archive, records):
        for shared_file in self.recurse_explicit_files(self.config.shared_data):
            record = archive.add_shared_file(shared_file)
            records.write(record)

    def write_metadata(self, archive, records, build_data, extra_dependencies=()):
        # <<< IMPORTANT >>>
        # Ensure calls are ordered by the number of path components followed by the name of the components

        # METADATA
        self.write_project_metadata(archive, records, extra_dependencies=extra_dependencies)

        # WHEEL
        self.write_archive_metadata(archive, records, build_data)

        # entry_points.txt
        self.write_entry_points_file(archive, records)

        # licenses/
        self.add_licenses(archive, records)

        # extra_metadata/ - write last
        self.add_extra_metadata(archive, records)

    def write_archive_metadata(self, archive, records, build_data):
        from packaging.tags import parse_tag

        metadata = f"""\
Wheel-Version: 1.0
Generator: hatchling {__version__}
Root-Is-Purelib: {'true' if build_data['pure_python'] else 'false'}
"""

        for tag in sorted(map(str, parse_tag(build_data['tag']))):
            metadata += f'Tag: {tag}\n'

        record = archive.write_metadata('WHEEL', metadata)
        records.write(record)

    def write_entry_points_file(self, archive, records):
        entry_points_file = self.construct_entry_points_file()
        if entry_points_file:
            record = archive.write_metadata('entry_points.txt', entry_points_file)
            records.write(record)

    def write_project_metadata(self, archive, records, extra_dependencies=()):
        record = archive.write_metadata(
            'METADATA', self.config.core_metadata_constructor(self.metadata, extra_dependencies=extra_dependencies)
        )
        records.write(record)

    def add_licenses(self, archive, records):
        for relative_path in self.metadata.core.license_files:
            license_file = os.path.normpath(os.path.join(self.root, relative_path))
            with open(license_file, 'rb') as f:
                record = archive.write_metadata(f'licenses/{relative_path}', f.read())
                records.write(record)

    def add_extra_metadata(self, archive, records):
        for extra_metadata_file in self.recurse_explicit_files(self.config.extra_metadata):
            record = archive.add_extra_metadata_file(extra_metadata_file)
            records.write(record)

    def construct_entry_points_file(self):
        core_metadata = self.metadata.core
        metadata_file = ''

        if core_metadata.scripts:
            metadata_file += '\n[console_scripts]\n'
            for name, object_ref in core_metadata.scripts.items():
                metadata_file += f'{name} = {object_ref}\n'

        if core_metadata.gui_scripts:
            metadata_file += '\n[gui_scripts]\n'
            for name, object_ref in core_metadata.gui_scripts.items():
                metadata_file += f'{name} = {object_ref}\n'

        if core_metadata.entry_points:
            for group, entry_points in core_metadata.entry_points.items():
                metadata_file += f'\n[{group}]\n'
                for name, object_ref in entry_points.items():
                    metadata_file += f'{name} = {object_ref}\n'

        return metadata_file.lstrip()

    def get_default_tag(self):
        supported_python_versions = []
        for major_version in get_known_python_major_versions():
            for minor_version in range(100):
                if self.metadata.core.python_constraint.contains(f'{major_version}.{minor_version}'):
                    supported_python_versions.append(f'py{major_version}')
                    break

        return f'{".".join(supported_python_versions)}-none-any'

    def get_default_build_data(self):
        return {'infer_tag': False, 'pure_python': True, 'dependencies': [], 'force_include_editable': {}}

    def get_forced_inclusion_map(self, build_data):
        if not build_data['force_include_editable']:
            return self.config.get_force_include()

        return normalize_inclusion_map(build_data['force_include_editable'], self.root)

    @property
    def artifact_project_id(self):
        return (
            self.project_id
            if self.config.strict_naming
            else f'{self.normalize_file_name_component(self.metadata.core.raw_name)}-{self.metadata.version}'
        )

    @classmethod
    def get_config_class(cls):
        return WheelBuilderConfig
