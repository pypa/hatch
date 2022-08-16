from __future__ import annotations

from abc import ABC, abstractmethod


class MetadataHookInterface(ABC):  # no cov
    """
    Example usage:

    === ":octicons-file-code-16: plugin.py"

        ```python
        from hatchling.metadata.plugin.interface import MetadataHookInterface


        class SpecialMetadataHook(MetadataHookInterface):
            PLUGIN_NAME = 'special'
            ...
        ```

    === ":octicons-file-code-16: hooks.py"

        ```python
        from hatchling.plugin import hookimpl

        from .plugin import SpecialMetadataHook


        @hookimpl
        def hatch_register_metadata_hook():
            return SpecialMetadataHook
        ```
    """

    PLUGIN_NAME = ''
    """The name used for selection."""

    def __init__(self, root, config):
        self.__root = root
        self.__config = config

    @property
    def root(self):
        """
        The root of the project tree.
        """
        return self.__root

    @property
    def config(self):
        """
        The hook configuration.

        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.metadata.hooks.<PLUGIN_NAME>]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [metadata.hooks.<PLUGIN_NAME>]
            ```
        """
        return self.__config

    @abstractmethod
    def update(self, metadata: dict):
        """
        This updates the metadata mapping of the `project` table in-place.
        """

    def get_known_classifiers(self) -> list[str]:
        """
        This returns extra classifiers that should be considered valid in addition to the ones known to PyPI.
        """
        return []
