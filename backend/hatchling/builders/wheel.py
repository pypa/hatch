import hashlib
import os
import stat
import sys
import tempfile
import zipfile
from contextlib import closing

from ..__about__ import __version__
from ..metadata.utils import DEFAULT_METADATA_VERSION, get_core_metadata_constructors
from .config import BuilderConfig
from .plugin.interface import BuilderInterface
from .utils import (
    format_file_hash,
    get_known_python_major_versions,
    get_reproducible_timestamp,
    normalize_archive_path,
    normalize_file_permissions,
    replace_file,
    set_zip_info_mode,
)

try:
    from io import StringIO
except ImportError:  # no cov
    from StringIO import StringIO

try:
    from editables import EditableProject
except ImportError:  # no cov
    EditableProject = None

EDITABLES_MINIMUM_VERSION = '0.2'


class WheelArchive(object):
    def __init__(self, metadata_directory, reproducible):
        """
        https://www.python.org/dev/peps/pep-0427/#abstract
        """
        self.metadata_directory = metadata_directory
        self.reproducible = reproducible
        if self.reproducible:
            self.time_tuple = self.get_reproducible_time_tuple()
        else:
            self.time_tuple = None

        raw_fd, self.path = tempfile.mkstemp(suffix='.whl')
        self.fd = os.fdopen(raw_fd, 'w+b')
        self.zf = zipfile.ZipFile(self.fd, 'w', compression=zipfile.ZIP_DEFLATED)

    if sys.version_info >= (3, 6):

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
            return relative_path, hash_digest, file_stat.st_size

    else:  # no cov

        @staticmethod
        def get_reproducible_time_tuple():
            from datetime import datetime

            d = datetime.utcfromtimestamp(get_reproducible_timestamp())
            return d.year, d.month, d.day, d.hour, d.minute, d.second

        def add_file(self, included_file):
            relative_path = normalize_archive_path(included_file.distribution_path)
            self.zf.write(included_file.path, arcname=relative_path)

            hash_obj = hashlib.sha256()
            with open(included_file.path, 'rb') as in_file:
                while True:
                    chunk = in_file.read(16384)
                    if not chunk:
                        break

                    hash_obj.update(chunk)

            hash_digest = format_file_hash(hash_obj.digest())
            return relative_path, hash_digest, os.stat(included_file.path).st_size

    def write_metadata(self, relative_path, contents):
        relative_path = '{}/{}'.format(self.metadata_directory, normalize_archive_path(relative_path))
        return self.write_file(relative_path, contents)

    def write_file(self, relative_path, contents):
        if not isinstance(contents, bytes):
            contents = contents.encode('utf-8')

        time_tuple = self.time_tuple or (2020, 2, 2, 0, 0, 0)
        zip_info = zipfile.ZipInfo(relative_path, time_tuple)
        set_zip_info_mode(zip_info)

        hash_obj = hashlib.sha256(contents)
        hash_digest = format_file_hash(hash_obj.digest())
        self.zf.writestr(zip_info, contents, compress_type=zipfile.ZIP_DEFLATED)

        return relative_path, hash_digest, len(contents)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.zf.close()
        self.fd.close()


class WheelBuilderConfig(BuilderConfig):
    def __init__(self, *args, **kwargs):
        super(WheelBuilderConfig, self).__init__(*args, **kwargs)

        self.__include_defined = bool(
            self.target_config.get('include', self.build_config.get('include'))
            or self.target_config.get('packages', self.build_config.get('packages'))
        )
        self.__include = []
        self.__exclude = []
        self.__packages = []

    def set_default_file_selection(self):
        if self.__include or self.__exclude or self.__packages:
            return

        project_name = self.builder.normalize_file_name_component(self.builder.metadata.core.name)
        if os.path.isfile(os.path.join(self.root, project_name, '__init__.py')):
            self.__include.append('/{}'.format(project_name))
        elif os.path.isfile(os.path.join(self.root, 'src', project_name, '__init__.py')):
            self.__packages.append('src/{}'.format(project_name))
        else:
            from glob import glob

            possible_namespace_packages = glob(os.path.join(self.root, '*', project_name, '__init__.py'))
            if possible_namespace_packages:
                relative_path = os.path.relpath(possible_namespace_packages[0], self.root)
                namespace = relative_path.split(os.path.sep)[0]
                self.__include.append('/{}'.format(namespace))
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


class WheelBuilder(BuilderInterface):
    """
    Build a binary distribution (.whl file)
    """

    PLUGIN_NAME = 'wheel'

    def __init__(self, *args, **kwargs):
        super(WheelBuilder, self).__init__(*args, **kwargs)

        self.__core_metadata_constructor = None
        self.__zip_safe = None

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

        metadata_directory = '{}.dist-info'.format(self.project_id)
        with WheelArchive(metadata_directory, self.config.reproducible) as archive, closing(StringIO()) as records:
            for included_file in self.recurse_project_files():
                record = archive.add_file(included_file)
                records.write(self.format_record(record))

            self.write_metadata(archive, records, build_data)

            records.write(u'{}/RECORD,,\n'.format(metadata_directory))
            archive.write_metadata('RECORD', records.getvalue())

        target = os.path.join(directory, '{}-{}.whl'.format(self.project_id, build_data['tag']))

        replace_file(archive.path, target)
        return target

    def build_editable(self, directory, **build_data):
        if sys.version_info[0] < 3 or self.config.dev_mode_dirs:
            return self.build_editable_pth(directory, **build_data)
        else:
            return self.build_editable_standard(directory, **build_data)

    def build_editable_standard(self, directory, **build_data):
        build_data['tag'] = self.get_default_tag()

        metadata_directory = '{}.dist-info'.format(self.project_id)
        with WheelArchive(metadata_directory, self.config.reproducible) as archive, closing(StringIO()) as records:
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
                    exposed_packages[distribution_module] = os.path.join(
                        self.root,
                        '{}{}'.format(relative_path[: relative_path.index(distribution_path)], distribution_module),
                    )

            editable_project = EditableProject(self.metadata.core.name.replace('-', '_'), self.root)
            for module, relative_path in exposed_packages.items():
                editable_project.map(module, relative_path)

            for filename, content in sorted(editable_project.files()):
                record = archive.write_file(filename, content)
                records.write(self.format_record(record))

            extra_dependencies = []
            for dependency in editable_project.dependencies():
                if dependency == 'editables':
                    dependency += '~={}'.format(EDITABLES_MINIMUM_VERSION)
                else:  # no cov
                    pass

                extra_dependencies.append(dependency)

            self.write_metadata(archive, records, build_data, extra_dependencies=extra_dependencies)

            records.write(u'{}/RECORD,,\n'.format(metadata_directory))
            archive.write_metadata('RECORD', records.getvalue())

        target = os.path.join(directory, '{}-{}.whl'.format(self.project_id, build_data['tag']))

        replace_file(archive.path, target)
        return target

    if sys.version_info[0] >= 3:

        def build_editable_pth(self, directory, **build_data):
            build_data['tag'] = self.get_default_tag()

            metadata_directory = '{}.dist-info'.format(self.project_id)
            with WheelArchive(metadata_directory, self.config.reproducible) as archive, closing(StringIO()) as records:
                editable_project = EditableProject(self.metadata.core.name.replace('-', '_'), self.root)

                for relative_directory in self.config.dev_mode_dirs:
                    editable_project.add_to_path(relative_directory)

                for filename, content in sorted(editable_project.files()):
                    record = archive.write_file(filename, content)
                    records.write(self.format_record(record))

                extra_dependencies = []
                for dependency in editable_project.dependencies():
                    if dependency == 'editables':
                        dependency += '~={}'.format(EDITABLES_MINIMUM_VERSION)
                    else:  # no cov
                        pass

                    extra_dependencies.append(dependency)

                self.write_metadata(archive, records, build_data, extra_dependencies=extra_dependencies)

                records.write(u'{}/RECORD,,\n'.format(metadata_directory))
                archive.write_metadata('RECORD', records.getvalue())

            target = os.path.join(directory, '{}-{}.whl'.format(self.project_id, build_data['tag']))

            replace_file(archive.path, target)
            return target

    else:  # no cov

        def build_editable_pth(self, directory, **build_data):
            build_data['tag'] = self.get_default_tag()

            metadata_directory = '{}.dist-info'.format(self.project_id)
            with WheelArchive(metadata_directory, self.config.reproducible) as archive, closing(StringIO()) as records:
                directories = []
                for relative_directory in self.config.dev_mode_dirs:
                    directories.append(os.path.normpath(os.path.join(self.root, relative_directory)))

                record = archive.write_file(
                    '{}.pth'.format(self.metadata.core.name.replace('-', '_')), '\n'.join(directories)
                )
                records.write(self.format_record(record))

                self.write_metadata(archive, records, build_data)

                records.write(u'{}/RECORD,,\n'.format(metadata_directory))
                archive.write_metadata('RECORD', records.getvalue())

            target = os.path.join(directory, '{}-{}.whl'.format(self.project_id, build_data['tag']))

            replace_file(archive.path, target)
            return target

    def write_metadata(self, archive, records, build_data, extra_dependencies=()):
        # <<< IMPORTANT >>>
        # Ensure calls are ordered by the number of path components followed by the name of the components

        # METADATA
        self.write_project_metadata(archive, records, extra_dependencies=extra_dependencies)

        # WHEEL
        self.write_archive_metadata(archive, records, build_data)

        # entry_points.txt
        self.write_entry_points_file(archive, records)

        # license_files/
        self.add_licenses(archive, records)

    def write_archive_metadata(self, archive, records, build_data):
        from packaging.tags import parse_tag

        metadata = 'Wheel-Version: 1.0\nGenerator: hatch {}\nRoot-Is-Purelib: {}\n'.format(
            __version__, 'true' if build_data.get('zip_safe', self.zip_safe) else 'false'
        )

        for tag in sorted(map(str, parse_tag(build_data['tag']))):
            metadata += 'Tag: {}\n'.format(tag)

        record = archive.write_metadata('WHEEL', metadata)
        records.write(self.format_record(record))

    def write_entry_points_file(self, archive, records):
        record = archive.write_metadata('entry_points.txt', self.construct_entry_points_file())
        records.write(self.format_record(record))

    def write_project_metadata(self, archive, records, extra_dependencies=()):
        record = archive.write_metadata(
            'METADATA', self.core_metadata_constructor(self.metadata, extra_dependencies=extra_dependencies)
        )
        records.write(self.format_record(record))

    def add_licenses(self, archive, records):
        for relative_path in self.metadata.core.license_files:
            license_file = os.path.normpath(os.path.join(self.root, relative_path))
            with open(license_file, 'rb') as f:
                record = archive.write_metadata('license_files/{}'.format(relative_path), f.read())
                records.write(self.format_record(record))

    def construct_entry_points_file(self):
        core_metadata = self.metadata.core
        metadata_file = ''

        if core_metadata.scripts:
            metadata_file += '\n[console_scripts]\n'
            for name, object_ref in core_metadata.scripts.items():
                metadata_file += '{} = {}\n'.format(name, object_ref)

        if core_metadata.gui_scripts:
            metadata_file += '\n[gui_scripts]\n'
            for name, object_ref in core_metadata.gui_scripts.items():
                metadata_file += '{} = {}\n'.format(name, object_ref)

        if core_metadata.entry_points:
            for group, entry_points in core_metadata.entry_points.items():
                metadata_file += '\n[{}]\n'.format(group)
                for name, object_ref in entry_points.items():
                    metadata_file += '{} = {}\n'.format(name, object_ref)

        return metadata_file.lstrip()

    def get_default_tag(self):
        supported_python_versions = []
        for major_version in get_known_python_major_versions():
            for minor_version in range(100):
                if self.metadata.core.python_constraint.contains('{}.{}'.format(major_version, minor_version)):
                    supported_python_versions.append('py{}'.format(major_version))
                    break

        return '{}-none-any'.format('.'.join(supported_python_versions))

    def get_default_build_data(self):
        return {'infer_tag': False}

    @property
    def core_metadata_constructor(self):
        if self.__core_metadata_constructor is None:
            core_metadata_version = self.target_config.get('core-metadata-version', DEFAULT_METADATA_VERSION)
            if not isinstance(core_metadata_version, str):
                raise TypeError(
                    'Field `tool.hatch.build.targets.{}.core-metadata-version` must be a string'.format(
                        self.PLUGIN_NAME
                    )
                )

            constructors = get_core_metadata_constructors()
            if core_metadata_version not in constructors:
                raise ValueError(
                    'Unknown metadata version `{}` for field `tool.hatch.build.targets.{}.core-metadata-version`. '
                    'Available: {}'.format(core_metadata_version, self.PLUGIN_NAME, ', '.join(sorted(constructors)))
                )

            self.__core_metadata_constructor = constructors[core_metadata_version]

        return self.__core_metadata_constructor

    @property
    def zip_safe(self):
        if self.__zip_safe is None:
            self.__zip_safe = bool(self.target_config.get('zip-safe', True))

        return self.__zip_safe

    @classmethod
    def get_config_class(cls):
        return WheelBuilderConfig

    @staticmethod
    def format_record(record):
        return u'{},sha256={},{}\n'.format(*record)
