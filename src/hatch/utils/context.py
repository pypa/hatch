import os
import string
from collections import ChainMap


class ContextFormatter(string.Formatter):
    def __init__(self, root):
        super().__init__()

        self.__root = str(root)

        # Allow subclasses to define their own formatters with precedence
        self.__formatters = ChainMap(
            {
                '/': self.__format_directory_separator,
                ';': self.__format_path_separator,
                'args': self.__format_args,
                'env': self.__format_env,
                'home': self.__format_home,
                'root': self.__format_root,
            }
        )

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
            return super().get_value(key, args, kwargs)

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

    def __format_directory_separator(self, value, data):
        return os.path.sep

    def __format_path_separator(self, value, data):
        return os.pathsep

    def __format_root(self, value, data):
        return self.__root

    def __format_home(self, value, data):
        return os.path.expanduser('~')

    def __format_env(self, value, data):
        env_var, separator, default = data.partition(':')
        if env_var in os.environ:
            return os.environ[env_var]
        elif not separator:
            raise ValueError(f'Environment variable without default must be set: {env_var}')
        else:
            return default

    def __format_args(self, value, data):
        if value is not None:
            return value
        else:
            return data or ''


class Context:
    def __init__(self, root, formatter=ContextFormatter):
        self.root = root

        self.__formatter = formatter(root)

    def format(self, *args, **kwargs):
        return self.__formatter.format(*args, **kwargs)
