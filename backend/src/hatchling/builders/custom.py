from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Generic

from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.metadata.core import ProjectMetadata
from hatchling.plugin.manager import PluginManagerBound
from hatchling.plugin.utils import load_plugin_from_script
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT

if TYPE_CHECKING:
    from hatchling.bridge.app import Application


class CustomBuilder(Generic[PluginManagerBound]):
    PLUGIN_NAME = 'custom'

    def __new__(  # type: ignore[misc]
        cls,
        root: str,
        plugin_manager: PluginManagerBound | None = None,
        config: dict[str, Any] | None = None,
        metadata: ProjectMetadata | None = None,
        app: Application | None = None,
    ) -> BuilderInterface:
        project_metadata = ProjectMetadata(root, plugin_manager, config)

        target_config = project_metadata.hatch.build_targets.get(cls.PLUGIN_NAME, {})
        if not isinstance(target_config, dict):
            message = f'Field `tool.hatch.build.targets.{cls.PLUGIN_NAME}` must be a table'
            raise TypeError(message)

        build_script = target_config.get('path', DEFAULT_BUILD_SCRIPT)
        if not isinstance(build_script, str):
            message = f'Option `path` for builder `{cls.PLUGIN_NAME}` must be a string'
            raise TypeError(message)

        if not build_script:
            message = f'Option `path` for builder `{cls.PLUGIN_NAME}` must not be empty if defined'
            raise ValueError(message)

        path = os.path.normpath(os.path.join(root, build_script))
        if not os.path.isfile(path):
            message = f'Build script does not exist: {build_script}'
            raise OSError(message)

        hook_class = load_plugin_from_script(path, build_script, BuilderInterface, 'builder')  # type: ignore[type-abstract]
        hook = hook_class(root, plugin_manager=plugin_manager, config=config, metadata=metadata, app=app)

        # Always keep the name to avoid confusion
        hook.PLUGIN_NAME = cls.PLUGIN_NAME

        return hook
