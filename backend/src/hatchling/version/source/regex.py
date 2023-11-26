from hatchling.version.core import VersionFile
from hatchling.version.source.plugin.interface import VersionSourceInterface


class RegexSource(VersionSourceInterface):
    PLUGIN_NAME = 'regex'

    def get_version_data(self) -> dict:
        relative_path = self.config.get('path', '')
        if not relative_path:
            message = 'option `path` must be specified'
            raise ValueError(message)

        if not isinstance(relative_path, str):
            message = 'option `path` must be a string'
            raise TypeError(message)

        pattern = self.config.get('pattern', '')
        if not isinstance(pattern, str):
            message = 'option `pattern` must be a string'
            raise TypeError(message)

        version_file = VersionFile(self.root, relative_path)
        version = version_file.read(pattern=pattern)

        return {'version': version, 'version_file': version_file}

    def set_version(self, version: str, version_data: dict) -> None:  # noqa: PLR6301
        version_data['version_file'].set_version(version)
