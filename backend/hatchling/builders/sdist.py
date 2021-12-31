import gzip
import os
import tarfile
import tempfile
from contextlib import closing
from copy import copy
from io import BytesIO
from time import time as get_current_timestamp

from ..metadata.utils import DEFAULT_METADATA_VERSION, get_core_metadata_constructors
from .plugin.interface import BuilderInterface
from .utils import get_reproducible_timestamp, normalize_archive_path, normalize_file_permissions, replace_file


class SdistArchive(object):
    def __init__(self, name, reproducible):
        """
        https://www.python.org/dev/peps/pep-0517/#source-distributions
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


class SdistBuilder(BuilderInterface):
    """
    Build an archive of the source files
    """

    PLUGIN_NAME = 'sdist'

    def __init__(self, *args, **kwargs):
        super(SdistBuilder, self).__init__(*args, **kwargs)

        self.__core_metadata_constructor = None
        self.__support_legacy = None

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
            for included_file in self.recurse_project_files():
                if self.support_legacy:
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

            archive.create_file(self.core_metadata_constructor(self.metadata), 'PKG-INFO')

            if self.support_legacy:
                archive.create_file(self.construct_setup_py_file(sorted(found_packages)), 'setup.py')

        target = os.path.join(directory, '{}.tar.gz'.format(self.project_id))

        replace_file(archive.path, target)
        return target

    def construct_setup_py_file(self, packages):
        contents = '# -*- coding: utf-8 -*-\nfrom setuptools import setup\n\n'

        contents += 'setup(\n'

        contents += '    name={!r},\n'.format(self.metadata.core.name)
        contents += '    version={!r},\n'.format(self.metadata.version)

        if self.metadata.core.description:
            contents += '    description={!r},\n'.format(self.metadata.core.description)

        if self.metadata.core.readme:
            contents += '    long_description={!r},\n'.format(self.metadata.core.readme)

        authors_data = self.metadata.core.authors_data
        if authors_data['name']:
            contents += '    author={!r},\n'.format(', '.join(authors_data['name']))
        if authors_data['email']:
            contents += '    author_email={!r},\n'.format(', '.join(authors_data['email']))

        maintainers_data = self.metadata.core.maintainers_data
        if maintainers_data['name']:
            contents += '    maintainer={!r},\n'.format(', '.join(maintainers_data['name']))
        if maintainers_data['email']:
            contents += '    maintainer_email={!r},\n'.format(', '.join(maintainers_data['email']))

        if self.metadata.core.classifiers:
            contents += '    classifiers=[\n'

            for classifier in self.metadata.core.classifiers:
                contents += '        {!r},\n'.format(classifier)

            contents += '    ],\n'

        if self.metadata.core.dependencies:
            contents += '    install_requires=[\n'

            for specifier in self.metadata.core.dependencies:
                contents += '        {!r},\n'.format(specifier)

            contents += '    ],\n'

        if self.metadata.core.optional_dependencies:
            contents += '    extras_require={\n'

            for option, specifiers in self.metadata.core.optional_dependencies.items():
                if not specifiers:
                    continue

                contents += '        {!r}: [\n'.format(option)

                for specifier in specifiers:
                    contents += '            {!r},\n'.format(specifier)

                contents += '        ],\n'

            contents += '    },\n'

        if self.metadata.core.scripts or self.metadata.core.gui_scripts or self.metadata.core.entry_points:
            contents += '    entry_points={\n'

            if self.metadata.core.scripts:
                contents += "        'console_scripts': [\n"

                for name, object_ref in self.metadata.core.scripts.items():
                    contents += '            {!r},\n'.format('{} = {}'.format(name, object_ref))

                contents += '        ],\n'

            if self.metadata.core.gui_scripts:
                contents += "        'gui_scripts': [\n"

                for name, object_ref in self.metadata.core.gui_scripts.items():
                    contents += '            {!r},\n'.format('{} = {}'.format(name, object_ref))

                contents += '        ],\n'

            if self.metadata.core.entry_points:
                for group, entry_points in self.metadata.core.entry_points.items():
                    contents += '        {!r}: [\n'.format(group)

                    for name, object_ref in entry_points.items():
                        contents += '            {!r},\n'.format('{} = {}'.format(name, object_ref))

                    contents += '        ],\n'

            contents += '    },\n'

        if packages:
            contents += '    packages=[\n'

            for package in packages:
                contents += '        {!r},\n'.format(package.replace(os.path.sep, '.'))

            contents += '    ],\n'

        contents += ')\n'

        return contents

    def get_default_build_data(self):
        build_data = {'artifacts': []}
        if not self.config.include_path('pyproject.toml'):
            build_data['artifacts'].append('/pyproject.toml')

        readme_path = self.metadata.core.readme_path
        if readme_path and not self.config.include_path(readme_path):
            build_data['artifacts'].append('/{}'.format(readme_path))

        license_files = self.metadata.core.license_files
        if license_files:
            for license_file in license_files:
                if not self.config.include_path(license_file):
                    build_data['artifacts'].append('/{}'.format(license_file))

        return build_data

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
    def support_legacy(self):
        if self.__support_legacy is None:
            self.__support_legacy = bool(self.target_config.get('support-legacy', False))

        return self.__support_legacy
