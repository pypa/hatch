from __future__ import annotations

import os
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.plugin.utils import load_plugin_from_script
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT


class CustomBuildHook:
    PLUGIN_NAME = 'custom'

    def __new__(  # type: ignore[misc]
        cls,
        root: str,
        config: dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> BuildHookInterface:
        build_script = config.get('path', DEFAULT_BUILD_SCRIPT)
        if not isinstance(build_script, str):
            message = f'Option `path` for build hook `{cls.PLUGIN_NAME}` must be a string'
            raise TypeError(message)

        if not build_script:
            message = f'Option `path` for build hook `{cls.PLUGIN_NAME}` must not be empty if defined'
            raise ValueError(message)

        path = os.path.normpath(os.path.join(root, build_script))
        if not os.path.isfile(path):
            message = f'Build script does not exist: {build_script}'
            raise OSError(message)

        hook_class = load_plugin_from_script(path, build_script, BuildHookInterface, 'build_hook')
        hook = hook_class(root, config, *args, **kwargs)

        # Always keep the name to avoid confusion
        hook.PLUGIN_NAME = cls.PLUGIN_NAME

        return hook
