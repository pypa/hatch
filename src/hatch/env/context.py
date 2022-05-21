from hatchling.utils.context import ContextFormatter


class EnvironmentContextFormatter(ContextFormatter):
    def __init__(self, environment):
        self.environment = environment
        self.CONTEXT_NAME = f'environment_{environment.PLUGIN_NAME}'

    def get_formatters(self):
        return {'args': self.__format_args, 'env_name': self.__format_env_name, 'verbosity': self.__format_verbosity}

    def __format_args(self, value, data):
        if value is not None:
            return value
        else:
            return data or ''

    def __format_env_name(self, value, data):
        return self.environment.name

    def __format_verbosity(self, value, data):
        return str(self.environment.verbosity)
