from abc import ABC, abstractmethod


class EnvironmentCollectorInterface(ABC):
    """
    Example usage:

    === ":octicons-file-code-16: plugin.py"

        ```python
        from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface


        class SpecialEnvironmentCollector(EnvironmentCollectorInterface):
            PLUGIN_NAME = 'special'
            ...
        ```

    === ":octicons-file-code-16: hooks.py"

        ```python
        from hatchling.plugin import hookimpl

        from .plugin import SpecialEnvironmentCollector


        @hookimpl
        def hatch_register_environment_collector():
            return SpecialEnvironmentCollector
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
            [tool.hatch.env.collectors.<PLUGIN_NAME>]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [env.collectors.<PLUGIN_NAME>]
            ```
        """
        return self.__config

    @abstractmethod
    def get_environment_config(self) -> dict:
        """
        Returns configuration for environments keyed by the environment name.
        """
