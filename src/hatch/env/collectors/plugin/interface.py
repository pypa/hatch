from __future__ import annotations

from abc import ABC


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

    def get_initial_config(self) -> dict[str, dict]:
        """
        Returns configuration for environments keyed by the environment name. Users and any subsequent collectors
        can override, but not remove, top level keys after this is called.
        """
        return {}

    def finalize_config(self, config: dict[str, dict]):
        """
        Finalizes configuration for environments keyed by the environment name. This will override
        any user-defined settings and any collectors that ran before this call.
        """
