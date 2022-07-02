import os
import string
from abc import ABC, abstractmethod
from collections import ChainMap
from contextlib import contextmanager

from hatchling.utils.fs import path_to_uri


class ContextFormatter(ABC):
    @abstractmethod
    def get_formatters(self):
        """
        This returns a mapping of supported field names to their respective formatting functions. Each function
        accepts 2 arguments:

        - the `value` that was passed to the format call, defaulting to `None`
        - the modifier `data`, defaulting to an empty string
        """

    @classmethod
    def format_path(cls, path, modifier):
        if not modifier:
            return os.path.normpath(path)
        elif modifier == 'uri':
            return path_to_uri(path)
        elif modifier == 'real':
            return os.path.realpath(path)
        else:
            raise ValueError(f'Unknown path modifier: {modifier}')


class DefaultContextFormatter(ContextFormatter):
    CONTEXT_NAME = 'default'

    def __init__(self, root):
        self.__root = root

    def get_formatters(self):
        return {
            '/': self.__format_directory_separator,
            ';': self.__format_path_separator,
            'env': self.__format_env,
            'home': self.__format_home,
            'root': self.__format_root,
        }

    def __format_directory_separator(self, value, data):
        return os.sep

    def __format_path_separator(self, value, data):
        return os.pathsep

    def __format_root(self, value, data):
        return self.format_path(self.__root, data)

    def __format_home(self, value, data):
        return self.format_path(os.path.expanduser('~'), data)

    def __format_env(self, value, data):
        if not data:
            raise ValueError('The `env` context formatting field requires a modifier')

        env_var, separator, default = data.partition(':')
        if env_var in os.environ:
            return os.environ[env_var]
        elif not separator:
            raise ValueError(f'Nonexistent environment variable must set a default: {env_var}')
        else:
            return default


class Context:
    def __init__(self, root):
        self.__root = str(root)

        # Allow callers to define their own formatters with precedence
        self.__formatters = ChainMap()
        self.__configured_contexts = set()
        self.__formatter = ContextStringFormatter(self.__formatters)

        self.add_context(DefaultContextFormatter(self.__root))

    def format(self, *args, **kwargs):
        return self.__formatter.format(*args, **kwargs)

    def add_context(self, context):
        if context.CONTEXT_NAME in self.__configured_contexts:
            return

        self.__add_formatters(context.get_formatters())
        self.__configured_contexts.add(context.CONTEXT_NAME)

    @contextmanager
    def apply_context(self, context):
        self.__add_formatters(context.get_formatters())
        try:
            yield
        finally:
            self.__remove_formatters()

    def __add_formatters(self, formatters):
        return self.__formatters.maps.insert(0, formatters)

    def __remove_formatters(self):
        if len(self.__formatters.maps) > 1:
            self.__formatters.maps.pop(0)


class ContextStringFormatter(string.Formatter):
    def __init__(self, formatters):
        super().__init__()

        self.__formatters = formatters

    def vformat(self, format_string, args, kwargs):
        # We override to increase the recursion limit from 2 to 10
        used_args = set()
        result, _ = self._vformat(format_string, args, kwargs, used_args, 10)
        self.check_unused_args(used_args, args, kwargs)
        return result

    def get_value(self, key, args, kwargs):
        if key in self.__formatters:
            # Avoid hard look-up and rely on `None` to indicate that the field is undefined
            return kwargs.get(key)
        else:
            try:
                return super().get_value(key, args, kwargs)
            except KeyError:
                raise ValueError(f'Unknown context field `{key}`') from None

    def format_field(self, value, format_spec):
        formatter, _, data = format_spec.partition(':')
        if formatter in self.__formatters:
            return self.__formatters[formatter](value, data)
        else:
            return super().format_field(value, format_spec)

    def parse(self, format_string):
        for literal_text, field_name, format_spec, conversion in super().parse(format_string):
            if field_name in self.__formatters:
                yield literal_text, field_name, f'{field_name}:{format_spec}', conversion
            else:
                yield literal_text, field_name, format_spec, conversion
