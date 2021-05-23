from abc import ABC, abstractmethod


class VersionSchemeInterface(ABC):  # no cov
    """
    Example usage:

    === ":octicons-file-code-16: plugin.py"

        ```python
        from hatch.version.scheme.plugin.interface import VersionSchemeInterface


        class SpecialVersionScheme(VersionSchemeInterface):
            PLUGIN_NAME = 'special'
            ...
        ```

    === ":octicons-file-code-16: hooks.py"

        ```python
        from hatchling.plugin import hookimpl

        from .plugin import SpecialVersionScheme


        @hookimpl
        def hatch_register_version_scheme():
            return SpecialVersionScheme
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
        The root of the project tree as a path-like object.
        """
        return self.__root

    @property
    def config(self) -> dict:
        """
        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.version]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [version]
            ```
        """
        return self.__config

    @abstractmethod
    def update(self, desired_version: str, original_version: str, version_data: dict):
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        This should return a normalized form of the desired version and verify that it
        is higher than the original version.
        """
