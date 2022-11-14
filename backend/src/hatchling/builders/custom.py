from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.metadata.core import ProjectMetadata
from hatchling.plugin.utils import load_plugin_from_script
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT

if TYPE_CHECKING:
    from hatchling.bridge.app import Application
    from hatchling.plugin.manager import PluginManager


class CustomBuilder:
    PLUGIN_NAME = 'custom'

    def __new__(
        cls,
        root: str,
        plugin_manager: PluginManager | None = None,
        config: dict[str, Any] | None = None,
        metadata: ProjectMetadata | None = None,
        app: Application | None = None,
    ) -> BuilderInterface:
        project_metadata = ProjectMetadata(root, plugin_manager, config)

        target_config = project_metadata.hatch.build_targets.get(cls.PLUGIN_NAME, {})
        if not isinstance(target_config, dict):
            raise TypeError(f'Field `tool.hatch.build.targets.{cls.PLUGIN_NAME}` must be a table')

        build_script = target_config.get('path', DEFAULT_BUILD_SCRIPT)
        if not isinstance(build_script, str):
            raise TypeError(f'Option `path` for builder `{cls.PLUGIN_NAME}` must be a string')
        elif not build_script:
            raise ValueError(f'Option `path` for builder `{cls.PLUGIN_NAME}` must not be empty if defined')

        path = os.path.normpath(os.path.join(root, build_script))
        if not os.path.isfile(path):
            raise OSError(f'Build script does not exist: {build_script}')

        hook_class = load_plugin_from_script(path, build_script, BuilderInterface, 'builder')
        hook = hook_class(root, plugin_manager=plugin_manager, config=config, metadata=metadata, app=app)

        # Always keep the name to avoid confusion
        hook.PLUGIN_NAME = cls.PLUGIN_NAME

        return hook
