from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, cast

from hatchling.builders.config import BuilderConfigBound

if TYPE_CHECKING:
    from hatchling.bridge.app import Application
    from hatchling.metadata.core import ProjectMetadata


class BuildHookInterface(Generic[BuilderConfigBound]):  # no cov
    """
    Example usage:

    ```python tab="plugin.py"
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface


    class SpecialBuildHook(BuildHookInterface):
        PLUGIN_NAME = 'special'
        ...
    ```

    ```python tab="hooks.py"
    from hatchling.plugin import hookimpl

    from .plugin import SpecialBuildHook


    @hookimpl
    def hatch_register_build_hook():
        return SpecialBuildHook
    ```
    """

    PLUGIN_NAME = ''
    """The name used for selection."""

    def __init__(
        self,
        root: str,
        config: dict[str, Any],
        build_config: BuilderConfigBound,
        metadata: ProjectMetadata,
        directory: str,
        target_name: str,
        app: Application | None = None,
    ) -> None:
        self.__root = root
        self.__config = config
        self.__build_config = build_config
        self.__metadata = metadata
        self.__directory = directory
        self.__target_name = target_name
        self.__app = app

    @property
    def app(self) -> Application:
        """
        An instance of [Application](../utilities.md#hatchling.bridge.app.Application).
        """
        if self.__app is None:
            from hatchling.bridge.app import Application

            self.__app = cast(Application, Application().get_safe_application())

        return self.__app

    @property
    def root(self) -> str:
        """
        The root of the project tree.
        """
        return self.__root

    @property
    def config(self) -> dict[str, Any]:
        """
        The cumulative hook configuration.

        ```toml config-example
        [tool.hatch.build.hooks.<PLUGIN_NAME>]
        [tool.hatch.build.targets.<TARGET_NAME>.hooks.<PLUGIN_NAME>]
        ```
        """
        return self.__config

    @property
    def metadata(self) -> ProjectMetadata:
        # Undocumented for now
        return self.__metadata

    @property
    def build_config(self) -> BuilderConfigBound:
        """
        An instance of [BuilderConfig](../utilities.md#hatchling.builders.config.BuilderConfig).
        """
        return self.__build_config

    @property
    def directory(self) -> str:
        """
        The build directory.
        """
        return self.__directory

    @property
    def target_name(self) -> str:
        """
        The plugin name of the build target.
        """
        return self.__target_name

    def dependencies(self) -> list[str]:  # noqa: PLR6301
        """
        A list of extra [dependencies](../../config/dependency.md) that must be installed
        prior to builds.

        !!! warning
            - For this to have any effect the hook dependency itself cannot be dynamic and
                must always be defined in `build-system.requires`.
            - As the hook must be imported to call this method, imports that require these
                dependencies must be evaluated lazily.
        """
        return []

    def clean(self, versions: list[str]) -> None:
        """
        This occurs before the build process if the `-c`/`--clean` flag was passed to
        the [`build`](../../cli/reference.md#hatch-build) command, or when invoking
        the [`clean`](../../cli/reference.md#hatch-clean) command.
        """

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """
        This occurs immediately before each build.

        Any modifications to the build data will be seen by the build target.
        """

    def finalize(self, version: str, build_data: dict[str, Any], artifact_path: str) -> None:
        """
        This occurs immediately after each build and will not run if the `--hooks-only` flag
        was passed to the [`build`](../../cli/reference.md#hatch-build) command.

        The build data will reflect any modifications done by the target during the build.
        """
