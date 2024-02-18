from __future__ import annotations

import os
import string
from abc import ABC, abstractmethod
from collections import ChainMap
from contextlib import contextmanager
from typing import Any, Iterable, Iterator, Mapping, MutableMapping, Sequence

from hatchling.utils.fs import path_to_uri


class ContextFormatter(ABC):
    @abstractmethod
    def get_formatters(self) -> MutableMapping:
        """
        This returns a mapping of supported field names to their respective formatting functions. Each function
        accepts 2 arguments:

        - the `value` that was passed to the format call, defaulting to `None`
        - the modifier `data`, defaulting to an empty string
        """

    @classmethod
    def format_path(cls, path: str, modifier: str) -> str:
        if not modifier:
            return os.path.normpath(path)

        modifiers = modifier.split(':')[::-1]
        while modifiers and modifiers[-1] == 'parent':
            path = os.path.dirname(path)
            modifiers.pop()

        if not modifiers:
            return path

        if len(modifiers) > 1:
            message = f'Expected a single path modifier and instead got: {", ".join(reversed(modifiers))}'
            raise ValueError(message)

        modifier = modifiers[0]
        if modifier == 'uri':
            return path_to_uri(path)

        if modifier == 'real':
            return os.path.realpath(path)

        message = f'Unknown path modifier: {modifier}'
        raise ValueError(message)


class DefaultContextFormatter(ContextFormatter):
    CONTEXT_NAME = 'default'

    def __init__(self, root: str) -> None:
        self.__root = root

    def get_formatters(self) -> MutableMapping:
        return {
            '/': self.__format_directory_separator,
            ';': self.__format_path_separator,
            'env': self.__format_env,
            'home': self.__format_home,
            'root': self.__format_root,
        }

    def __format_directory_separator(self, value: str, data: str) -> str:  # noqa: ARG002, PLR6301
        return os.sep

    def __format_path_separator(self, value: str, data: str) -> str:  # noqa: ARG002, PLR6301
        return os.pathsep

    def __format_root(self, value: str, data: str) -> str:  # noqa: ARG002
        return self.format_path(self.__root, data)

    def __format_home(self, value: str, data: str) -> str:  # noqa: ARG002
        return self.format_path(os.path.expanduser('~'), data)

    def __format_env(self, value: str, data: str) -> str:  # noqa: ARG002, PLR6301
        if not data:
            message = 'The `env` context formatting field requires a modifier'
            raise ValueError(message)

        env_var, separator, default = data.partition(':')
        if env_var in os.environ:
            return os.environ[env_var]

        if not separator:
            message = f'Nonexistent environment variable must set a default: {env_var}'
            raise ValueError(message)

        return default


class Context:
    def __init__(self, root: str) -> None:
        self.__root = str(root)

        # Allow callers to define their own formatters with precedence
        self.__formatters: ChainMap = ChainMap()
        self.__configured_contexts: set[str] = set()
        self.__formatter = ContextStringFormatter(self.__formatters)

        self.add_context(DefaultContextFormatter(self.__root))

    def format(self, *args: Any, **kwargs: Any) -> str:
        return self.__formatter.format(*args, **kwargs)

    def add_context(self, context: DefaultContextFormatter) -> None:
        if context.CONTEXT_NAME in self.__configured_contexts:
            return

        self.__add_formatters(context.get_formatters())
        self.__configured_contexts.add(context.CONTEXT_NAME)

    @contextmanager
    def apply_context(self, context: DefaultContextFormatter) -> Iterator:
        self.__add_formatters(context.get_formatters())
        try:
            yield
        finally:
            self.__remove_formatters()

    def __add_formatters(self, formatters: MutableMapping) -> None:
        return self.__formatters.maps.insert(0, formatters)

    def __remove_formatters(self) -> None:
        if len(self.__formatters.maps) > 1:
            self.__formatters.maps.pop(0)


class ContextStringFormatter(string.Formatter):
    def __init__(self, formatters: ChainMap) -> None:
        super().__init__()

        self.__formatters = formatters

    def vformat(self, format_string: str, args: Sequence[Any], kwargs: Mapping[str, Any]) -> str:
        # We override to increase the recursion limit from 2 to 10
        #
        # TODO: remove type ignore after https://github.com/python/typeshed/pull/9228
        used_args = set()  # type: ignore[var-annotated]
        result, _ = self._vformat(format_string, args, kwargs, used_args, 10)
        self.check_unused_args(used_args, args, kwargs)
        return result

    def get_value(self, key: int | str, args: Sequence[Any], kwargs: Mapping[str, Any]) -> Any:
        if key in self.__formatters:
            # Avoid hard look-up and rely on `None` to indicate that the field is undefined
            return kwargs.get(str(key))

        try:
            return super().get_value(key, args, kwargs)
        except KeyError:
            message = f'Unknown context field `{key}`'
            raise ValueError(message) from None

    def format_field(self, value: Any, format_spec: str) -> Any:
        formatter, _, data = format_spec.partition(':')
        if formatter in self.__formatters:
            return self.__formatters[formatter](value, data)

        return super().format_field(value, format_spec)

    def parse(self, format_string: str) -> Iterable:
        for literal_text, field_name, format_spec, conversion in super().parse(format_string):
            if field_name in self.__formatters:
                yield literal_text, field_name, f'{field_name}:{format_spec}', conversion
            else:
                yield literal_text, field_name, format_spec, conversion
