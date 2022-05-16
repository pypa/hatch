import gzip
import os
import tarfile
import tempfile
from contextlib import closing
from copy import copy
from io import BytesIO
from time import time as get_current_timestamp

from ..metadata.spec import DEFAULT_METADATA_VERSION, get_core_metadata_constructors
from ..utils.constants import DEFAULT_BUILD_SCRIPT, DEFAULT_CONFIG_FILE
from .config import BuilderConfig
from .plugin.interface import BuilderInterface
from .utils import get_reproducible_timestamp, normalize_archive_path, normalize_file_permissions, replace_file


class SdistArchive:
    def __init__(self, name, reproducible):
        """
        https://peps.python.org/pep-0517/#source-distributions
        """
        self.name = name
        self.reproducible = reproducible

        if reproducible:
            self.timestamp = get_reproducible_timestamp()
        else:
            self.timestamp = None

        raw_fd, self.path = tempfile.mkstemp(suffix='.tar.gz')
        self.fd = os.fdopen(raw_fd, 'w+b')
        self.gz = gzip.GzipFile(fileobj=self.fd, mode='wb', mtime=self.timestamp)
        self.tf = tarfile.TarFile(fileobj=self.gz, mode='w', format=tarfile.PAX_FORMAT)
        self.gettarinfo = lambda *args, **kwargs: self.normalize_tar_metadata(self.tf.gettarinfo(*args, **kwargs))

    def create_file(self, contents, *relative_paths):
        contents = contents.encode('utf-8')
        tar_info = tarfile.TarInfo(normalize_archive_path(os.path.join(self.name, *relative_paths)))
        tar_info.mtime = self.timestamp if self.reproducible else int(get_current_timestamp())
        tar_info.size = len(contents)

        with closing(BytesIO(contents)) as buffer:
            self.tf.addfile(tar_info, buffer)

    def normalize_tar_metadata(self, tar_info):
        if not self.reproducible:
            return tar_info

        tar_info = copy(tar_info)
        tar_info.uid = 0
        tar_info.gid = 0
        tar_info.uname = ''
        tar_info.gname = ''
        tar_info.mode = normalize_file_permissions(tar_info.mode)
        tar_info.mtime = self.timestamp

        return tar_info

    def __getattr__(self, name):
        attr = getattr(self.tf, name)
        setattr(self, name, attr)
        return attr

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.tf.close()
        self.gz.close()
        self.fd.close()


class SdistBuilderConfig(BuilderConfig):
    def __init__(self, *args, **kwargs):
        super(SdistBuilderConfig, self).__init__(*args, **kwargs)

        self.__core_metadata_constructor = None
        self.__support_legacy = None

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
    def support_legacy(self):
        if self.__support_legacy is None:
            self.__support_legacy = bool(self.target_config.get('support-legacy', False))

        return self.__support_legacy


class SdistBuilder(BuilderInterface):
    """
    Build an archive of the source files
    """

    PLUGIN_NAME = 'sdist'

    def get_version_api(self):
        return {'standard': self.build_standard}

    def get_default_versions(self):
        return ['standard']

    def clean(self, directory, versions):
        for filename in os.listdir(directory):
            if filename.endswith('.tar.gz'):
                os.remove(os.path.join(directory, filename))

    def build_standard(self, directory, **build_data):
        found_packages = set()

        with SdistArchive(self.project_id, self.config.reproducible) as archive:
            for included_file in self.recurse_included_files():
                if self.config.support_legacy:
                    possible_package, file_name = os.path.split(included_file.relative_path)
                    if file_name == '__init__.py':
                        found_packages.add(possible_package)

                tar_info = archive.gettarinfo(
                    included_file.path,
                    arcname=normalize_archive_path(os.path.join(self.project_id, included_file.distribution_path)),
                )

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

        target = os.path.join(directory, f'{self.project_id}.tar.gz')

        replace_file(archive.path, target)
        return target

    def construct_setup_py_file(self, packages, extra_dependencies=()):
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

            for specifier in dependencies:
                specifier = specifier.replace("'", '"')
                contents += f'        {specifier!r},\n'

            contents += '    ],\n'

        if self.metadata.core.optional_dependencies:
            contents += '    extras_require={\n'

            for option, specifiers in self.metadata.core.optional_dependencies.items():
                if not specifiers:
                    continue

                contents += f'        {option!r}: [\n'

                for specifier in specifiers:
                    specifier = specifier.replace("'", '"')
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
            contents += '    packages=[\n'

            for package in packages:
                contents += f"        {package.replace(os.path.sep, '.')!r},\n"

            contents += '    ],\n'

        contents += ')\n'

        return contents

    def get_default_build_data(self):
        build_data = {'artifacts': [], 'force_include': {}, 'dependencies': []}

        for exclusion_files in self.config.vcs_exclusion_files.values():
            for exclusion_file in exclusion_files:
                build_data['force_include'][exclusion_file] = os.path.basename(exclusion_file)

        # Check for inclusion first to avoid redundant pattern matching
        if not self.config.include_path('pyproject.toml'):
            build_data['artifacts'].append('/pyproject.toml')

        readme_path = self.metadata.core.readme_path
        if readme_path and not self.config.include_path(readme_path):
            build_data['artifacts'].append(f'/{readme_path}')

        license_files = self.metadata.core.license_files
        if license_files:
            for license_file in license_files:
                if not self.config.include_path(license_file):
                    build_data['artifacts'].append(f'/{license_file}')

        if not self.config.include_path(DEFAULT_BUILD_SCRIPT):
            build_data['artifacts'].append(f'/{DEFAULT_BUILD_SCRIPT}')

        if not self.config.include_path(DEFAULT_CONFIG_FILE):
            build_data['artifacts'].append(f'/{DEFAULT_CONFIG_FILE}')

        return build_data

    @classmethod
    def get_config_class(cls):
        return SdistBuilderConfig
