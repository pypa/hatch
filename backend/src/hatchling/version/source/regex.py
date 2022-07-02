from hatchling.version.core import VersionFile
from hatchling.version.source.plugin.interface import VersionSourceInterface


class RegexSource(VersionSourceInterface):
    PLUGIN_NAME = 'regex'

    def get_version_data(self):
        relative_path = self.config.get('path', '')
        if not relative_path:
            raise ValueError('option `path` must be specified')
        elif not isinstance(relative_path, str):
            raise TypeError('option `path` must be a string')

        pattern = self.config.get('pattern', '')
        if not isinstance(pattern, str):
            raise TypeError('option `pattern` must be a string')

        version_file = VersionFile(self.root, relative_path)
        version = version_file.read(pattern)

        return {'version': version, 'version_file': version_file}

    def set_version(self, version, version_data):
        version_data['version_file'].set_version(version)
