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
                raise TypeError('Option `path` for build hook `{}` must be a string'.format(self.PLUGIN_NAME))
            elif not path:
                raise ValueError('Option `path` for build hook `{}` is required'.format(self.PLUGIN_NAME))

            self.__config_path = path

        return self.__config_path

    @property
    def config_template(self):
        if self.__config_template is None:
            template = self.config.get('template', '')
            if not isinstance(template, str):
                raise TypeError('Option `template` for build hook `{}` must be a string'.format(self.PLUGIN_NAME))

            self.__config_template = template

        return self.__config_template

    @property
    def config_pattern(self):
        if self.__config_pattern is None:
            pattern = self.config.get('pattern', '')
            if not isinstance(pattern, (str, bool)):
                raise TypeError(
                    'Option `pattern` for build hook `{}` must be a string or boolean'.format(self.PLUGIN_NAME)
                )

            self.__config_pattern = pattern

        return self.__config_pattern

    def initialize(self, version, build_data):
        version_file = VersionFile(self.root, self.config_path)
        if self.config_pattern:
            version_file.read(self.config_pattern)
            version_file.set_version(self.metadata.version)
        else:
            version_file.write(self.metadata.version, self.config_template)

        build_data['artifacts'].append('/{}'.format(self.config_path))
