import os
import re
from io import open

from .plugin.interface import VersionSourceInterface

DEFAULT_PATTERN = r'^(__version__|VERSION) *= *([\'"])v?(?P<version>.+?)\2'


class RegexSource(VersionSourceInterface):
    PLUGIN_NAME = 'regex'

    def get_version_data(self):
        relative_path = self.config.get('path')
        if not relative_path:
            raise ValueError('option `path` must be specified')
        elif not isinstance(relative_path, str):
            raise TypeError('option `path` must be a string')

        path = os.path.normpath(os.path.join(self.root, relative_path))
        if not os.path.isfile(path):
            raise OSError('file does not exist: {}'.format(relative_path))

        pattern = self.config.get('pattern') or DEFAULT_PATTERN
        if not isinstance(pattern, str):
            raise TypeError('option `pattern` must be a string')

        with open(path, 'r', encoding='utf-8') as f:
            contents = f.read()

        match = re.search(pattern, contents, flags=re.MULTILINE)
        if not match:
            raise ValueError('unable to parse the version from the file: {}'.format(relative_path))

        groups = match.groupdict()
        if 'version' not in groups:
            raise ValueError('no group named `version` was defined in the pattern')

        return {'version': groups['version'], 'file_contents': contents, 'version_location': match.span('version')}

    def set_version(self, version, version_data):
        file_contents = version_data['file_contents']
        start, end = version_data['version_location']

        with open(self.config['path'], 'w', encoding='utf-8') as f:
            # TODO: f.write(f'{file_contents[:start]}{version}{file_contents[end:]}')
            f.write('{}{}{}'.format(file_contents[:start], version, file_contents[end:]))
