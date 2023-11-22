from __future__ import annotations


class EnvironmentCollectorInterface:
    """
    Example usage:

    ```python tab="plugin.py"
        from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface


        class SpecialEnvironmentCollector(EnvironmentCollectorInterface):
            PLUGIN_NAME = 'special'
            ...
    ```

    ```python tab="hooks.py"
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
        ```toml config-example
        [tool.hatch.env.collectors.<PLUGIN_NAME>]
        ```
        """
        return self.__config

    def get_initial_config(self) -> dict[str, dict]:  # noqa: PLR6301
        """
        Returns configuration for environments keyed by the environment or matrix name.
        """
        return {}

    def finalize_config(self, config: dict[str, dict]):
        """
        Finalizes configuration for environments keyed by the environment or matrix name. This will override
        any user-defined settings and any collectors that ran before this call.

        This is called before matrices are turned into concrete environments.
        """

    def finalize_environments(self, config: dict[str, dict]):
        """
        Finalizes configuration for environments keyed by the environment name. This will override
        any user-defined settings and any collectors that ran before this call.

        This is called after matrices are turned into concrete environments.
        """
