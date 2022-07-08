from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.version.core import VersionFile


class VersionBuildHook(BuildHookInterface):
    PLUGIN_NAME = 'version'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__config_path = None
        self.__config_template = None
        self.__config_pattern = None

    @property
    def config_path(self):
        if self.__config_path is None:
            path = self.config.get('path', '')
            if not isinstance(path, str):
                raise TypeError(f'Option `path` for build hook `{self.PLUGIN_NAME}` must be a string')
            elif not path:
                raise ValueError(f'Option `path` for build hook `{self.PLUGIN_NAME}` is required')

            self.__config_path = path

        return self.__config_path

    @property
    def config_template(self):
        if self.__config_template is None:
            template = self.config.get('template', '')
            if not isinstance(template, str):
                raise TypeError(f'Option `template` for build hook `{self.PLUGIN_NAME}` must be a string')

            self.__config_template = template

        return self.__config_template

    @property
    def config_pattern(self):
        if self.__config_pattern is None:
            pattern = self.config.get('pattern', '')
            if not isinstance(pattern, (str, bool)):
                raise TypeError(f'Option `pattern` for build hook `{self.PLUGIN_NAME}` must be a string or boolean')

            self.__config_pattern = pattern

        return self.__config_pattern

    def initialize(self, version, build_data):
        version_file = VersionFile(self.root, self.config_path)
        if self.config_pattern:
            version_file.read(self.config_pattern)
            version_file.set_version(self.metadata.version)
        else:
            version_file.write(self.metadata.version, self.config_template)

        build_data['artifacts'].append(f'/{self.config_path}')
