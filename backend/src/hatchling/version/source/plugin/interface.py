from __future__ import annotations

from abc import ABC, abstractmethod


class VersionSourceInterface(ABC):  # no cov
    """
    Example usage:

    ```python tab="plugin.py"
    from hatchling.version.source.plugin.interface import VersionSourceInterface


    class SpecialVersionSource(VersionSourceInterface):
        PLUGIN_NAME = 'special'
        ...
    ```

    ```python tab="hooks.py"
    from hatchling.plugin import hookimpl

    from .plugin import SpecialVersionSource


    @hookimpl
    def hatch_register_version_source():
        return SpecialVersionSource
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
    def get_version_data(self) -> dict:
        """
        This should return a mapping with a `version` key representing the current version of the project and will be
        displayed when invoking the [`version`](../../cli/reference.md#hatch-version) command without any arguments.

        The mapping can contain anything else and will be passed to
        [set_version](reference.md#hatchling.version.source.plugin.interface.VersionSourceInterface.set_version)
        when updating the version.
        """

    def set_version(self, version: str, version_data: dict) -> None:
        """
        This should update the version to the first argument with the data provided during retrieval.
        """
        raise NotImplementedError
