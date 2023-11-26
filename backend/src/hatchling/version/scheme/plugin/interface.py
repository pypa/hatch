from __future__ import annotations

from abc import ABC, abstractmethod


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

    @abstractmethod
    def update(self, desired_version: str, original_version: str, version_data: dict) -> str:
        """
        This should return a normalized form of the desired version and verify that it
        is higher than the original version.
        """
