from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MetadataHookInterface(ABC):  # no cov
    """
    Example usage:

    ```python tab="plugin.py"
    from hatchling.metadata.plugin.interface import MetadataHookInterface


    class SpecialMetadataHook(MetadataHookInterface):
        PLUGIN_NAME = "special"
        ...
    ```

    ```python tab="hooks.py"
    from hatchling.plugin import hookimpl

    from .plugin import SpecialMetadataHook


    @hookimpl
    def hatch_register_metadata_hook():
        return SpecialMetadataHook
    ```
    """

    PLUGIN_NAME = ""
    """The name used for selection."""

    def __init__(self, root: str, config: dict, config_settings: dict[str, Any] | None) -> None:
        self.__root = root
        self.__config = config
        self.__config_settings = config_settings

    @property
    def root(self) -> str:
        """
        The root of the project tree.
        """
        return self.__root

    @property
    def config(self) -> dict:
        """
        The hook configuration.

        ```toml config-example
        [tool.hatch.metadata.hooks.<PLUGIN_NAME>]
        ```
        """
        return self.__config

    @property
    def config_settings(self) -> dict[str, Any] | None:
        """
        Configuration settings from the build frontend, if supported.
        """
        return self.__config_settings

    @abstractmethod
    def update(self, metadata: dict) -> None:
        """
        This updates the metadata mapping of the `project` table in-place.
        """

    def get_known_classifiers(self) -> list[str]:  # noqa: PLR6301
        """
        This returns extra classifiers that should be considered valid in addition to the ones known to PyPI.
        """
        return []
