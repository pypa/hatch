from __future__ import annotations

import os
from abc import ABC, abstractmethod
from functools import cached_property


class VersionSchemeInterface(ABC):  # no cov
    """
    Example usage:

    ```python tab="plugin.py"
    from hatchling.version.scheme.plugin.interface import VersionSchemeInterface


    class SpecialVersionScheme(VersionSchemeInterface):
        PLUGIN_NAME = 'special'
        ...
    ```

    ```python tab="hooks.py"
    from hatchling.plugin import hookimpl

    from .plugin import SpecialVersionScheme


    @hookimpl
    def hatch_register_version_scheme():
        return SpecialVersionScheme
    ```
    """

    PLUGIN_NAME = ''
    """The name used for selection."""

    def __init__(self, root: str, config: dict) -> None:
        self.__root = root
        self.__config = config

    @property
    def root(self) -> str:
        """
        The root of the project tree as a string.
        """
        return self.__root

    @property
    def config(self) -> dict:
        """
        ```toml config-example
        [tool.hatch.version]
        ```
        """
        return self.__config

    @cached_property
    def validate_bump(self) -> bool:
        """
        This is the value of the `validate-bump` option, with the `HATCH_VERSION_VALIDATE_BUMP`
        environment variable taking precedence. Validation is enabled by default.

        ```toml config-example
        [tool.hatch.version]
        validate-bump = true
        ```
        """
        from hatchling.utils.constants import VersionEnvVars

        if VersionEnvVars.VALIDATE_BUMP in os.environ:
            return os.environ[VersionEnvVars.VALIDATE_BUMP] not in {'false', '0'}

        validate_bump = self.config.get('validate-bump', True)
        if not isinstance(validate_bump, bool):
            message = 'option `validate-bump` must be a boolean'
            raise TypeError(message)

        return validate_bump

    @abstractmethod
    def update(self, desired_version: str, original_version: str, version_data: dict) -> str:
        """
        This should return a normalized form of the desired version. If the
        [validate_bump](reference.md#hatchling.version.scheme.plugin.interface.VersionSchemeInterface.validate_bump)
        property is `True`, this method should also verify that the version is higher than the original version.
        """
