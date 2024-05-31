from __future__ import annotations

import gzip
import os
import tarfile
import tempfile
from contextlib import closing
from copy import copy
from io import BytesIO
from time import time as get_current_timestamp
from typing import TYPE_CHECKING, Any, Callable

from hatchling.builders.config import BuilderConfig
from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.builders.utils import (
    get_reproducible_timestamp,
    normalize_archive_path,
    normalize_artifact_permissions,
    normalize_file_permissions,
    normalize_relative_path,
    replace_file,
)
from hatchling.metadata.spec import DEFAULT_METADATA_VERSION, get_core_metadata_constructors
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT, DEFAULT_CONFIG_FILE

if TYPE_CHECKING:
    from types import TracebackType


class SdistArchive:
    def __init__(self, name: str, *, reproducible: bool) -> None:
        """
        https://peps.python.org/pep-0517/#source-distributions
        """
        self.name = name
        self.reproducible = reproducible
        self.timestamp: int | None = get_reproducible_timestamp() if reproducible else None

        raw_fd, self.path = tempfile.mkstemp(suffix='.tar.gz')
        self.fd = os.fdopen(raw_fd, 'w+b')
        self.gz = gzip.GzipFile(fileobj=self.fd, mode='wb', mtime=self.timestamp)
        self.tf = tarfile.TarFile(fileobj=self.gz, mode='w', format=tarfile.PAX_FORMAT)
        self.gettarinfo = lambda *args, **kwargs: self.normalize_tar_metadata(self.tf.gettarinfo(*args, **kwargs))

    def create_file(self, contents: str | bytes, *relative_paths: str) -> None:
        if not isinstance(contents, bytes):
            contents = contents.encode('utf-8')
        tar_info = tarfile.TarInfo(normalize_archive_path(os.path.join(self.name, *relative_paths)))
        tar_info.size = len(contents)
        if self.reproducible and self.timestamp is not None:
            tar_info.mtime = self.timestamp
        else:
            tar_info.mtime = int(get_current_timestamp())

        with closing(BytesIO(contents)) as buffer:
            self.tf.addfile(tar_info, buffer)

    def normalize_tar_metadata(self, tar_info: tarfile.TarInfo | None) -> tarfile.TarInfo | None:
        if not self.reproducible or tar_info is None:
            return tar_info

        tar_info = copy(tar_info)
        tar_info.uid = 0
        tar_info.gid = 0
        tar_info.uname = ''
        tar_info.gname = ''
        tar_info.mode = normalize_file_permissions(tar_info.mode)
        if self.timestamp is not None:
            tar_info.mtime = self.timestamp

        return tar_info

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self.tf, name)
        setattr(self, name, attr)
        return attr

    def __enter__(self) -> SdistArchive:  # noqa: PYI034
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.tf.close()
        self.gz.close()
        self.fd.close()


class SdistBuilderConfig(BuilderConfig):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.__core_metadata_constructor: Callable[..., str] | None = None
        self.__strict_naming: bool | None = None
        self.__support_legacy: bool | None = None

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
    def support_legacy(self) -> bool:
        if self.__support_legacy is None:
            self.__support_legacy = bool(self.target_config.get('support-legacy', False))

        return self.__support_legacy


class SdistBuilder(BuilderInterface):
    """
    Build an archive of the source files
    """

    PLUGIN_NAME = 'sdist'

    def get_version_api(self) -> dict[str, Callable]:
        return {'standard': self.build_standard}

    def get_default_versions(self) -> list[str]:  # noqa: PLR6301
        return ['standard']

    def clean(  # noqa: PLR6301
        self,
        directory: str,
        versions: list[str],  # noqa: ARG002
    ) -> None:
        for filename in os.listdir(directory):
            if filename.endswith('.tar.gz'):
                os.remove(os.path.join(directory, filename))

    def build_standard(self, directory: str, **build_data: Any) -> str:
        found_packages = set()

        with SdistArchive(self.artifact_project_id, reproducible=self.config.reproducible) as archive:
            for included_file in self.recurse_included_files():
                if self.config.support_legacy:
                    possible_package, file_name = os.path.split(included_file.relative_path)
                    if file_name == '__init__.py':
                        found_packages.add(possible_package)

                tar_info = archive.gettarinfo(
                    included_file.path,
                    arcname=normalize_archive_path(
                        os.path.join(self.artifact_project_id, included_file.distribution_path)
                    ),
                )
                if tar_info is None:  # no cov
                    continue

                if tar_info.isfile():
                    with open(included_file.path, 'rb') as f:
                        archive.addfile(tar_info, f)
                else:  # no cov
                    # TODO: Investigate if this is necessary (for symlinks, etc.)
                    archive.addfile(tar_info)

            archive.create_file(
                self.config.core_metadata_constructor(self.metadata, extra_dependencies=build_data['dependencies']),
                'PKG-INFO',
            )

            if self.config.support_legacy:
                archive.create_file(
                    self.construct_setup_py_file(sorted(found_packages), extra_dependencies=build_data['dependencies']),
                    'setup.py',
                )

        target = os.path.join(directory, f'{self.artifact_project_id}.tar.gz')

        replace_file(archive.path, target)
        normalize_artifact_permissions(target)
        return target

    @property
    def artifact_project_id(self) -> str:
        return (
            self.project_id
            if self.config.strict_naming
            else f'{self.normalize_file_name_component(self.metadata.core.raw_name)}-{self.metadata.version}'
        )

    def construct_setup_py_file(self, packages: list[str], extra_dependencies: tuple[()] = ()) -> str:
        contents = '# -*- coding: utf-8 -*-\nfrom setuptools import setup\n\n'

        contents += 'setup(\n'

        contents += f'    name={self.metadata.core.name!r},\n'
        contents += f'    version={self.metadata.version!r},\n'

        if self.metadata.core.description:
            contents += f'    description={self.metadata.core.description!r},\n'

        if self.metadata.core.readme:
            contents += f'    long_description={self.metadata.core.readme!r},\n'

        authors_data = self.metadata.core.authors_data
        if authors_data['name']:
            contents += f"    author={', '.join(authors_data['name'])!r},\n"
        if authors_data['email']:
            contents += f"    author_email={', '.join(authors_data['email'])!r},\n"

        maintainers_data = self.metadata.core.maintainers_data
        if maintainers_data['name']:
            contents += f"    maintainer={', '.join(maintainers_data['name'])!r},\n"
        if maintainers_data['email']:
            contents += f"    maintainer_email={', '.join(maintainers_data['email'])!r},\n"

        if self.metadata.core.classifiers:
            contents += '    classifiers=[\n'

            for classifier in self.metadata.core.classifiers:
                contents += f'        {classifier!r},\n'

            contents += '    ],\n'

        dependencies = list(self.metadata.core.dependencies)
        dependencies.extend(extra_dependencies)
        if dependencies:
            contents += '    install_requires=[\n'

            for raw_specifier in dependencies:
                specifier = raw_specifier.replace("'", '"')
                contents += f'        {specifier!r},\n'

            contents += '    ],\n'

        if self.metadata.core.optional_dependencies:
            contents += '    extras_require={\n'

            for option, specifiers in self.metadata.core.optional_dependencies.items():
                if not specifiers:
                    continue

                contents += f'        {option!r}: [\n'

                for raw_specifier in specifiers:
                    specifier = raw_specifier.replace("'", '"')
                    contents += f'            {specifier!r},\n'

                contents += '        ],\n'

            contents += '    },\n'

        if self.metadata.core.scripts or self.metadata.core.gui_scripts or self.metadata.core.entry_points:
            contents += '    entry_points={\n'

            if self.metadata.core.scripts:
                contents += "        'console_scripts': [\n"

                for name, object_ref in self.metadata.core.scripts.items():
                    contents += f"            '{name} = {object_ref}',\n"

                contents += '        ],\n'

            if self.metadata.core.gui_scripts:
                contents += "        'gui_scripts': [\n"

                for name, object_ref in self.metadata.core.gui_scripts.items():
                    contents += f"            '{name} = {object_ref}',\n"

                contents += '        ],\n'

            if self.metadata.core.entry_points:
                for group, entry_points in self.metadata.core.entry_points.items():
                    contents += f'        {group!r}: [\n'

                    for name, object_ref in entry_points.items():
                        contents += f"            '{name} = {object_ref}',\n"

                    contents += '        ],\n'

            contents += '    },\n'

        if packages:
            src_layout = False
            contents += '    packages=[\n'

            for package in packages:
                if package.startswith(f'src{os.sep}'):
                    src_layout = True
                    contents += f"        {package.replace(os.sep, '.')[4:]!r},\n"
                else:
                    contents += f"        {package.replace(os.sep, '.')!r},\n"

            contents += '    ],\n'

            if src_layout:
                contents += "    package_dir={'': 'src'},\n"

        contents += ')\n'

        return contents

    def get_default_build_data(self) -> dict[str, Any]:
        force_include = {}
        for filename in ['pyproject.toml', DEFAULT_CONFIG_FILE, DEFAULT_BUILD_SCRIPT]:
            path = os.path.join(self.root, filename)
            if os.path.exists(path):
                force_include[path] = filename
        build_data = {'force_include': force_include, 'dependencies': []}

        for exclusion_files in self.config.vcs_exclusion_files.values():
            for exclusion_file in exclusion_files:
                force_include[exclusion_file] = os.path.basename(exclusion_file)

        readme_path = self.metadata.core.readme_path
        if readme_path:
            readme_path = normalize_relative_path(readme_path)
            force_include[os.path.join(self.root, readme_path)] = readme_path

        license_files = self.metadata.core.license_files
        if license_files:
            for license_file in license_files:
                relative_path = normalize_relative_path(license_file)
                force_include[os.path.join(self.root, relative_path)] = relative_path

        return build_data

    @classmethod
    def get_config_class(cls) -> type[SdistBuilderConfig]:
        return SdistBuilderConfig
