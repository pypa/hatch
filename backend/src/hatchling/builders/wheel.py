from __future__ import annotations

import csv
import hashlib
import os
import stat
import sys
import tempfile
import zipfile
from functools import cached_property
from io import StringIO
from typing import TYPE_CHECKING, Any, Callable, Iterable, NamedTuple, Sequence, Tuple, cast

from hatchling.__about__ import __version__
from hatchling.builders.config import BuilderConfig
from hatchling.builders.constants import EDITABLES_REQUIREMENT
from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.builders.utils import (
    format_file_hash,
    get_known_python_major_versions,
    get_reproducible_timestamp,
    normalize_archive_path,
    normalize_artifact_permissions,
    normalize_file_permissions,
    normalize_inclusion_map,
    replace_file,
    set_zip_info_mode,
)
from hatchling.metadata.spec import DEFAULT_METADATA_VERSION, get_core_metadata_constructors

if TYPE_CHECKING:
    from types import TracebackType

    from hatchling.builders.plugin.interface import IncludedFile


TIME_TUPLE = Tuple[int, int, int, int, int, int]


class FileSelectionOptions(NamedTuple):
    include: list[str]
    exclude: list[str]
    packages: list[str]
    only_include: list[str]


class RecordFile:
    def __init__(self) -> None:
        self.__file_obj = StringIO()
        self.__writer = csv.writer(self.__file_obj, delimiter=',', quotechar='"', lineterminator='\n')

    def write(self, record: Iterable[Any]) -> None:
        self.__writer.writerow(record)

    def construct(self) -> str:
        return self.__file_obj.getvalue()

    def __enter__(self) -> RecordFile:  # noqa: PYI034
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.__file_obj.close()


class WheelArchive:
    def __init__(self, project_id: str, *, reproducible: bool) -> None:
        """
        https://peps.python.org/pep-0427/#abstract
        """
        self.metadata_directory = f'{project_id}.dist-info'
        self.shared_data_directory = f'{project_id}.data'
        self.time_tuple: TIME_TUPLE | None = None

        self.reproducible = reproducible
        if self.reproducible:
            self.time_tuple = self.get_reproducible_time_tuple()
        else:
            self.time_tuple = None

        raw_fd, self.path = tempfile.mkstemp(suffix='.whl')
        self.fd = os.fdopen(raw_fd, 'w+b')
        self.zf = zipfile.ZipFile(self.fd, 'w', compression=zipfile.ZIP_DEFLATED)

    @staticmethod
    def get_reproducible_time_tuple() -> TIME_TUPLE:
        from datetime import datetime, timezone

        d = datetime.fromtimestamp(get_reproducible_timestamp(), timezone.utc)
        return d.year, d.month, d.day, d.hour, d.minute, d.second

    def add_file(self, included_file: IncludedFile) -> tuple[str, str, str]:
        relative_path = normalize_archive_path(included_file.distribution_path)
        file_stat = os.stat(included_file.path)

        if self.reproducible:
            zip_info = zipfile.ZipInfo(relative_path, cast(TIME_TUPLE, self.time_tuple))

            # https://github.com/takluyver/flit/pull/66
            new_mode = normalize_file_permissions(file_stat.st_mode)
            set_zip_info_mode(zip_info, new_mode)
            if stat.S_ISDIR(file_stat.st_mode):  # no cov
                zip_info.external_attr |= 0x10
            else:
                zip_info.file_size = file_stat.st_size
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

    def write_metadata(self, relative_path: str, contents: str | bytes) -> tuple[str, str, str]:
        relative_path = f'{self.metadata_directory}/{normalize_archive_path(relative_path)}'
        return self.write_file(relative_path, contents)

    def write_shared_script(self, included_file: IncludedFile, contents: str | bytes) -> tuple[str, str, str]:
        relative_path = (
            f'{self.shared_data_directory}/scripts/{normalize_archive_path(included_file.distribution_path)}'
        )
        if sys.platform == 'win32':
            return self.write_file(relative_path, contents)

        file_stat = os.stat(included_file.path)
        return self.write_file(
            relative_path,
            contents,
            mode=normalize_file_permissions(file_stat.st_mode) if self.reproducible else file_stat.st_mode,
        )

    def add_shared_file(self, shared_file: IncludedFile) -> tuple[str, str, str]:
        shared_file.distribution_path = f'{self.shared_data_directory}/data/{shared_file.distribution_path}'
        return self.add_file(shared_file)

    def add_extra_metadata_file(self, extra_metadata_file: IncludedFile) -> tuple[str, str, str]:
        extra_metadata_file.distribution_path = (
            f'{self.metadata_directory}/extra_metadata/{extra_metadata_file.distribution_path}'
        )
        return self.add_file(extra_metadata_file)

    def write_file(
        self,
        relative_path: str,
        contents: str | bytes,
        *,
        mode: int | None = None,
    ) -> tuple[str, str, str]:
        if not isinstance(contents, bytes):
            contents = contents.encode('utf-8')

        time_tuple = self.time_tuple or (2020, 2, 2, 0, 0, 0)
        zip_info = zipfile.ZipInfo(relative_path, time_tuple)
        if mode is None:
            set_zip_info_mode(zip_info)
        else:
            set_zip_info_mode(zip_info, mode)

        hash_obj = hashlib.sha256(contents)
        hash_digest = format_file_hash(hash_obj.digest())
        self.zf.writestr(zip_info, contents, compress_type=zipfile.ZIP_DEFLATED)

        return relative_path, f'sha256={hash_digest}', str(len(contents))

    def __enter__(self) -> WheelArchive:  # noqa: PYI034
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.zf.close()
        self.fd.close()


class WheelBuilderConfig(BuilderConfig):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.__core_metadata_constructor: Callable[..., str] | None = None
        self.__shared_data: dict[str, str] | None = None
        self.__shared_scripts: dict[str, str] | None = None
        self.__extra_metadata: dict[str, str] | None = None
        self.__strict_naming: bool | None = None
        self.__macos_max_compat: bool | None = None

    @cached_property
    def default_file_selection_options(self) -> FileSelectionOptions:
        include = self.target_config.get('include', self.build_config.get('include', []))
        exclude = self.target_config.get('exclude', self.build_config.get('exclude', []))
        packages = self.target_config.get('packages', self.build_config.get('packages', []))
        only_include = self.target_config.get('only-include', self.build_config.get('only-include', []))

        if include or packages or only_include:
            return FileSelectionOptions(include, exclude, packages, only_include)

        project_names: set[str] = set()
        for project_name in (
            self.builder.normalize_file_name_component(self.builder.metadata.core.raw_name),
            self.builder.normalize_file_name_component(self.builder.metadata.core.name),
        ):
            if os.path.isfile(os.path.join(self.root, project_name, '__init__.py')):
                normalized_project_name = self.get_raw_fs_path_name(self.root, project_name)
                return FileSelectionOptions([], exclude, [normalized_project_name], [])

            if os.path.isfile(os.path.join(self.root, 'src', project_name, '__init__.py')):
                normalized_project_name = self.get_raw_fs_path_name(os.path.join(self.root, 'src'), project_name)
                return FileSelectionOptions([], exclude, [f'src/{normalized_project_name}'], [])

            module_file = f'{project_name}.py'
            if os.path.isfile(os.path.join(self.root, module_file)):
                return FileSelectionOptions([], exclude, [], [module_file])

            from glob import glob

            possible_namespace_packages = glob(os.path.join(self.root, '*', project_name, '__init__.py'))
            if len(possible_namespace_packages) == 1:
                relative_path = os.path.relpath(possible_namespace_packages[0], self.root)
                namespace = relative_path.split(os.sep)[0]
                return FileSelectionOptions([], exclude, [namespace], [])
            project_names.add(project_name)

        if self.bypass_selection or self.build_artifact_spec is not None or self.get_force_include():
            self.set_exclude_all()
            return FileSelectionOptions([], exclude, [], [])

        project_names_text = ' or '.join(sorted(project_names))
        message = (
            f'Unable to determine which files to ship inside the wheel using the following heuristics: '
            f'https://hatch.pypa.io/latest/plugins/builder/wheel/#default-file-selection\n\n'
            f'The most likely cause of this is that there is no directory that matches the name of your '
            f'project ({project_names_text}).\n\n'
            f'At least one file selection option must be defined in the `tool.hatch.build.targets.wheel` '
            f'table, see: https://hatch.pypa.io/latest/config/build/\n\n'
            f'As an example, if you intend to ship a directory named `foo` that resides within a `src` '
            f'directory located at the root of your project, you can define the following:\n\n'
            f'[tool.hatch.build.targets.wheel]\n'
            f'packages = ["src/foo"]'
        )
        raise ValueError(message)

    def default_include(self) -> list[str]:
        return self.default_file_selection_options.include

    def default_exclude(self) -> list[str]:
        return self.default_file_selection_options.exclude

    def default_packages(self) -> list[str]:
        return self.default_file_selection_options.packages

    def default_only_include(self) -> list[str]:
        return self.default_file_selection_options.only_include

    @property
    def core_metadata_constructor(self) -> Callable[..., str]:
        if self.__core_metadata_constructor is None:
            core_metadata_version = self.target_config.get('core-metadata-version', DEFAULT_METADATA_VERSION)
            if not isinstance(core_metadata_version, str):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.core-metadata-version` must be a string'
                raise TypeError(message)

            constructors = get_core_metadata_constructors()
            if core_metadata_version not in constructors:
                message = (
                    f'Unknown metadata version `{core_metadata_version}` for field '
                    f'`tool.hatch.build.targets.{self.plugin_name}.core-metadata-version`. '
                    f'Available: {", ".join(sorted(constructors))}'
                )
                raise ValueError(message)

            self.__core_metadata_constructor = constructors[core_metadata_version]

        return self.__core_metadata_constructor

    @property
    def shared_data(self) -> dict[str, str]:
        if self.__shared_data is None:
            shared_data = self.target_config.get('shared-data', {})
            if not isinstance(shared_data, dict):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.shared-data` must be a mapping'
                raise TypeError(message)

            for i, (source, relative_path) in enumerate(shared_data.items(), 1):
                if not source:
                    message = (
                        f'Source #{i} in field `tool.hatch.build.targets.{self.plugin_name}.shared-data` '
                        f'cannot be an empty string'
                    )
                    raise ValueError(message)

                if not isinstance(relative_path, str):
                    message = (
                        f'Path for source `{source}` in field '
                        f'`tool.hatch.build.targets.{self.plugin_name}.shared-data` must be a string'
                    )
                    raise TypeError(message)

                if not relative_path:
                    message = (
                        f'Path for source `{source}` in field '
                        f'`tool.hatch.build.targets.{self.plugin_name}.shared-data` cannot be an empty string'
                    )
                    raise ValueError(message)

            self.__shared_data = normalize_inclusion_map(shared_data, self.root)

        return self.__shared_data

    @property
    def shared_scripts(self) -> dict[str, str]:
        if self.__shared_scripts is None:
            shared_scripts = self.target_config.get('shared-scripts', {})
            if not isinstance(shared_scripts, dict):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.shared-scripts` must be a mapping'
                raise TypeError(message)

            for i, (source, relative_path) in enumerate(shared_scripts.items(), 1):
                if not source:
                    message = (
                        f'Source #{i} in field `tool.hatch.build.targets.{self.plugin_name}.shared-scripts` '
                        f'cannot be an empty string'
                    )
                    raise ValueError(message)

                if not isinstance(relative_path, str):
                    message = (
                        f'Path for source `{source}` in field '
                        f'`tool.hatch.build.targets.{self.plugin_name}.shared-scripts` must be a string'
                    )
                    raise TypeError(message)

                if not relative_path:
                    message = (
                        f'Path for source `{source}` in field '
                        f'`tool.hatch.build.targets.{self.plugin_name}.shared-scripts` cannot be an empty string'
                    )
                    raise ValueError(message)

            self.__shared_scripts = normalize_inclusion_map(shared_scripts, self.root)

        return self.__shared_scripts

    @property
    def extra_metadata(self) -> dict[str, str]:
        if self.__extra_metadata is None:
            extra_metadata = self.target_config.get('extra-metadata', {})
            if not isinstance(extra_metadata, dict):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.extra-metadata` must be a mapping'
                raise TypeError(message)

            for i, (source, relative_path) in enumerate(extra_metadata.items(), 1):
                if not source:
                    message = (
                        f'Source #{i} in field `tool.hatch.build.targets.{self.plugin_name}.extra-metadata` '
                        f'cannot be an empty string'
                    )
                    raise ValueError(message)

                if not isinstance(relative_path, str):
                    message = (
                        f'Path for source `{source}` in field '
                        f'`tool.hatch.build.targets.{self.plugin_name}.extra-metadata` must be a string'
                    )
                    raise TypeError(message)

                if not relative_path:
                    message = (
                        f'Path for source `{source}` in field '
                        f'`tool.hatch.build.targets.{self.plugin_name}.extra-metadata` cannot be an empty string'
                    )
                    raise ValueError(message)

            self.__extra_metadata = normalize_inclusion_map(extra_metadata, self.root)

        return self.__extra_metadata

    @property
    def strict_naming(self) -> bool:
        if self.__strict_naming is None:
            if 'strict-naming' in self.target_config:
                strict_naming = self.target_config['strict-naming']
                if not isinstance(strict_naming, bool):
                    message = f'Field `tool.hatch.build.targets.{self.plugin_name}.strict-naming` must be a boolean'
                    raise TypeError(message)
            else:
                strict_naming = self.build_config.get('strict-naming', True)
                if not isinstance(strict_naming, bool):
                    message = 'Field `tool.hatch.build.strict-naming` must be a boolean'
                    raise TypeError(message)

            self.__strict_naming = strict_naming

        return self.__strict_naming

    @property
    def macos_max_compat(self) -> bool:
        if self.__macos_max_compat is None:
            macos_max_compat = self.target_config.get('macos-max-compat', False)
            if not isinstance(macos_max_compat, bool):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.macos-max-compat` must be a boolean'
                raise TypeError(message)

            self.__macos_max_compat = macos_max_compat

        return self.__macos_max_compat

    @cached_property
    def bypass_selection(self) -> bool:
        bypass_selection = self.target_config.get('bypass-selection', False)
        if not isinstance(bypass_selection, bool):
            message = f'Field `tool.hatch.build.targets.{self.plugin_name}.bypass-selection` must be a boolean'
            raise TypeError(message)

        return bypass_selection

    if sys.platform in {'darwin', 'win32'}:

        @staticmethod
        def get_raw_fs_path_name(directory: str, name: str) -> str:
            normalized = name.casefold()
            entries = os.listdir(directory)
            for entry in entries:
                if entry.casefold() == normalized:
                    return entry

            return name  # no cov

    else:

        @staticmethod
        def get_raw_fs_path_name(directory: str, name: str) -> str:  # noqa: ARG004
            return name


class WheelBuilder(BuilderInterface):
    """
    Build a binary distribution (.whl file)
    """

    PLUGIN_NAME = 'wheel'

    def get_version_api(self) -> dict[str, Callable]:
        return {'standard': self.build_standard, 'editable': self.build_editable}

    def get_default_versions(self) -> list[str]:  # noqa: PLR6301
        return ['standard']

    def clean(  # noqa: PLR6301
        self,
        directory: str,
        versions: list[str],  # noqa: ARG002
    ) -> None:
        for filename in os.listdir(directory):
            if filename.endswith('.whl'):
                os.remove(os.path.join(directory, filename))

    def build_standard(self, directory: str, **build_data: Any) -> str:
        if 'tag' not in build_data:
            if build_data['infer_tag']:
                build_data['tag'] = self.get_best_matching_tag()
            else:
                build_data['tag'] = self.get_default_tag()

        with WheelArchive(
            self.artifact_project_id, reproducible=self.config.reproducible
        ) as archive, RecordFile() as records:
            for included_file in self.recurse_included_files():
                record = archive.add_file(included_file)
                records.write(record)

            self.write_data(archive, records, build_data, build_data['dependencies'])

            records.write((f'{archive.metadata_directory}/RECORD', '', ''))
            archive.write_metadata('RECORD', records.construct())

        target = os.path.join(directory, f"{self.artifact_project_id}-{build_data['tag']}.whl")

        replace_file(archive.path, target)
        normalize_artifact_permissions(target)
        return target

    def build_editable(self, directory: str, **build_data: Any) -> str:
        if self.config.dev_mode_dirs:
            return self.build_editable_explicit(directory, **build_data)

        return self.build_editable_detection(directory, **build_data)

    def build_editable_detection(self, directory: str, **build_data: Any) -> str:
        from editables import EditableProject

        build_data['tag'] = self.get_default_tag()

        with WheelArchive(
            self.artifact_project_id, reproducible=self.config.reproducible
        ) as archive, RecordFile() as records:
            exposed_packages = {}
            for included_file in self.recurse_selected_project_files():
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
                            f'{relative_path[: relative_path.index(distribution_path)]}{distribution_module}',
                        )
                    except ValueError:
                        message = (
                            'Dev mode installations are unsupported when any path rewrite in the `sources` option '
                            'changes a prefix rather than removes it, see: '
                            'https://github.com/pfmoore/editables/issues/20'
                        )
                        raise ValueError(message) from None

            editable_project = EditableProject(self.metadata.core.name, self.root)

            if self.config.dev_mode_exact:
                for module, relative_path in exposed_packages.items():
                    editable_project.map(module, relative_path)
            else:
                for relative_path in exposed_packages.values():
                    editable_project.add_to_path(os.path.dirname(relative_path))

            for raw_filename, content in sorted(editable_project.files()):
                filename = raw_filename
                if filename.endswith('.pth') and not filename.startswith('_'):
                    filename = f'_{filename}'

                record = archive.write_file(filename, content)
                records.write(record)

            for included_file in self.recurse_forced_files(self.get_forced_inclusion_map(build_data)):
                record = archive.add_file(included_file)
                records.write(record)

            extra_dependencies = list(build_data['dependencies'])
            for raw_dependency in editable_project.dependencies():
                dependency = raw_dependency
                if dependency == 'editables':
                    dependency = EDITABLES_REQUIREMENT
                else:  # no cov
                    pass

                extra_dependencies.append(dependency)

            self.write_data(archive, records, build_data, extra_dependencies)

            records.write((f'{archive.metadata_directory}/RECORD', '', ''))
            archive.write_metadata('RECORD', records.construct())

        target = os.path.join(directory, f"{self.artifact_project_id}-{build_data['tag']}.whl")

        replace_file(archive.path, target)
        normalize_artifact_permissions(target)
        return target

    def build_editable_explicit(self, directory: str, **build_data: Any) -> str:
        build_data['tag'] = self.get_default_tag()

        with WheelArchive(
            self.artifact_project_id, reproducible=self.config.reproducible
        ) as archive, RecordFile() as records:
            directories = sorted(
                os.path.normpath(os.path.join(self.root, relative_directory))
                for relative_directory in self.config.dev_mode_dirs
            )

            record = archive.write_file(f"_{self.metadata.core.name.replace('-', '_')}.pth", '\n'.join(directories))
            records.write(record)

            for included_file in self.recurse_forced_files(self.get_forced_inclusion_map(build_data)):
                record = archive.add_file(included_file)
                records.write(record)

            self.write_data(archive, records, build_data, build_data['dependencies'])

            records.write((f'{archive.metadata_directory}/RECORD', '', ''))
            archive.write_metadata('RECORD', records.construct())

        target = os.path.join(directory, f"{self.artifact_project_id}-{build_data['tag']}.whl")

        replace_file(archive.path, target)
        normalize_artifact_permissions(target)
        return target

    def write_data(
        self, archive: WheelArchive, records: RecordFile, build_data: dict[str, Any], extra_dependencies: Sequence[str]
    ) -> None:
        self.add_shared_data(archive, records, build_data)
        self.add_shared_scripts(archive, records, build_data)

        # Ensure metadata is written last, see https://peps.python.org/pep-0427/#recommended-archiver-features
        self.write_metadata(archive, records, build_data, extra_dependencies=extra_dependencies)

    def add_shared_data(self, archive: WheelArchive, records: RecordFile, build_data: dict[str, Any]) -> None:
        shared_data = dict(self.config.shared_data)
        shared_data.update(normalize_inclusion_map(build_data['shared_data'], self.root))

        for shared_file in self.recurse_explicit_files(shared_data):
            record = archive.add_shared_file(shared_file)
            records.write(record)

    def add_shared_scripts(self, archive: WheelArchive, records: RecordFile, build_data: dict[str, Any]) -> None:
        import re
        from io import BytesIO

        # https://packaging.python.org/en/latest/specifications/binary-distribution-format/#recommended-installer-features
        shebang = re.compile(rb'^#!.*(?:pythonw?|pypyw?)[0-9.]*(.*)', flags=re.DOTALL)

        shared_scripts = dict(self.config.shared_scripts)
        shared_scripts.update(normalize_inclusion_map(build_data['shared_scripts'], self.root))

        for shared_script in self.recurse_explicit_files(shared_scripts):
            with open(shared_script.path, 'rb') as f:
                content = BytesIO()
                for line in f:
                    # Ignore leading blank lines
                    if not line.strip():
                        continue

                    match = shebang.match(line)
                    if match is None:
                        content.write(line)
                    else:
                        content.write(b'#!python')
                        if remaining := match.group(1):
                            content.write(remaining)

                    content.write(f.read())
                    break

            record = archive.write_shared_script(shared_script, content.getvalue())
            records.write(record)

    def write_metadata(
        self,
        archive: WheelArchive,
        records: RecordFile,
        build_data: dict[str, Any],
        extra_dependencies: Sequence[str] = (),
    ) -> None:
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
        self.add_extra_metadata(archive, records, build_data)

    @staticmethod
    def write_archive_metadata(archive: WheelArchive, records: RecordFile, build_data: dict[str, Any]) -> None:
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

    def write_entry_points_file(self, archive: WheelArchive, records: RecordFile) -> None:
        entry_points_file = self.construct_entry_points_file()
        if entry_points_file:
            record = archive.write_metadata('entry_points.txt', entry_points_file)
            records.write(record)

    def write_project_metadata(
        self, archive: WheelArchive, records: RecordFile, extra_dependencies: Sequence[str] = ()
    ) -> None:
        record = archive.write_metadata(
            'METADATA', self.config.core_metadata_constructor(self.metadata, extra_dependencies=extra_dependencies)
        )
        records.write(record)

    def add_licenses(self, archive: WheelArchive, records: RecordFile) -> None:
        for relative_path in self.metadata.core.license_files:
            license_file = os.path.normpath(os.path.join(self.root, relative_path))
            with open(license_file, 'rb') as f:
                record = archive.write_metadata(f'licenses/{relative_path}', f.read())
                records.write(record)

    def add_extra_metadata(self, archive: WheelArchive, records: RecordFile, build_data: dict[str, Any]) -> None:
        extra_metadata = dict(self.config.extra_metadata)
        extra_metadata.update(normalize_inclusion_map(build_data['extra_metadata'], self.root))

        for extra_metadata_file in self.recurse_explicit_files(extra_metadata):
            record = archive.add_extra_metadata_file(extra_metadata_file)
            records.write(record)

    def construct_entry_points_file(self) -> str:
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

    def get_default_tag(self) -> str:
        known_major_versions = list(get_known_python_major_versions())
        max_version_part = 100
        supported_python_versions = []
        for major_version in known_major_versions:
            for minor_version in range(max_version_part):
                # Try an artificially high patch version to account for common cases like `>=3.11.4` or `>=3.10,<3.11`
                if self.metadata.core.python_constraint.contains(f'{major_version}.{minor_version}.{max_version_part}'):
                    supported_python_versions.append(f'py{major_version}')
                    break

        # Slow path, try all permutations to account for narrow support ranges like `<=3.11.4`
        if not supported_python_versions:
            for major_version in known_major_versions:
                for minor_version in range(max_version_part):
                    for patch_version in range(max_version_part):
                        if self.metadata.core.python_constraint.contains(
                            f'{major_version}.{minor_version}.{patch_version}'
                        ):
                            supported_python_versions.append(f'py{major_version}')
                            break
                    else:
                        continue
                    break

        return f'{".".join(supported_python_versions)}-none-any'

    def get_best_matching_tag(self) -> str:
        import sys

        from packaging.tags import sys_tags

        # Linux tag is after many/musl; packaging tools are required to skip
        # many/musl, see https://github.com/pypa/packaging/issues/160
        tag = next(iter(t for t in sys_tags() if 'manylinux' not in t.platform and 'musllinux' not in t.platform))
        tag_parts = [tag.interpreter, tag.abi, tag.platform]

        if sys.platform == 'darwin':
            from hatchling.builders.macos import process_macos_plat_tag

            tag_parts[2] = process_macos_plat_tag(tag_parts[2], compat=self.config.macos_max_compat)

        return '-'.join(tag_parts)

    def get_default_build_data(self) -> dict[str, Any]:  # noqa: PLR6301
        return {
            'infer_tag': False,
            'pure_python': True,
            'dependencies': [],
            'force_include_editable': {},
            'extra_metadata': {},
            'shared_data': {},
            'shared_scripts': {},
        }

    def get_forced_inclusion_map(self, build_data: dict[str, Any]) -> dict[str, str]:
        if not build_data['force_include_editable']:
            return self.config.get_force_include()

        return normalize_inclusion_map(build_data['force_include_editable'], self.root)

    @property
    def artifact_project_id(self) -> str:
        return (
            self.project_id
            if self.config.strict_naming
            else f'{self.normalize_file_name_component(self.metadata.core.raw_name)}-{self.metadata.version}'
        )

    @classmethod
    def get_config_class(cls) -> type[WheelBuilderConfig]:
        return WheelBuilderConfig
