from abc import ABC, abstractmethod

from hatchling.utils.context import ContextFormatter


class EnvironmentContextFormatterBase(ContextFormatter, ABC):
    @abstractmethod
    def formatters(self):
        return {}


class EnvironmentContextFormatter(EnvironmentContextFormatterBase):
    def __init__(self, environment):
        self.environment = environment
        self.CONTEXT_NAME = f'environment_{environment.PLUGIN_NAME}'

    def formatters(self):
        """
        This returns a mapping of supported field names to their respective formatting functions. Each function
        accepts 2 arguments:

        - the `value` that was passed to the format call, defaulting to `None`
        - the modifier `data`, defaulting to an empty string
        """
        return {}

    def get_formatters(self):
        formatters = {
            'args': self.__format_args,
            'env_name': self.__format_env_name,
            'verbosity': self.__format_verbosity,
        }
        formatters.update(self.formatters())
        return formatters

    def __format_args(self, value, data):
        if value is not None:
            return value
        else:
            return data or ''

    def __format_env_name(self, value, data):
        return self.environment.name

    def __format_verbosity(self, value, data):
        return str(self.environment.verbosity)
