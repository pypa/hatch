from abc import ABC, abstractmethod

from hatch.env.utils import get_verbosity_flag
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
            'env_type': self.__format_env_type,
            'matrix': self.__format_matrix,
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

    def __format_env_type(self, value, data):
        return self.environment.PLUGIN_NAME

    def __format_matrix(self, value, data):
        if not data:
            raise ValueError('The `matrix` context formatting field requires a modifier')

        variable, separator, default = data.partition(':')
        if variable in self.environment.matrix_variables:
            return self.environment.matrix_variables[variable]
        elif not separator:
            raise ValueError(f'Nonexistent matrix variable must set a default: {variable}')
        else:
            return default

    def __format_verbosity(self, value, data):
        if not data:
            return str(self.environment.verbosity)

        modifier, _, adjustment = data.partition(':')
        if modifier != 'flag':
            raise ValueError(f'Unknown verbosity modifier: {modifier}')
        elif not adjustment:
            adjustment = '0'

        try:
            adjustment = int(adjustment)
        except ValueError:
            raise TypeError(f'Verbosity flag adjustment must be an integer: {adjustment}') from None

        return get_verbosity_flag(self.environment.verbosity, adjustment=adjustment)
