from __future__ import annotations

import os
from typing import Any

from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface
from hatch.plugin.constants import DEFAULT_CUSTOM_SCRIPT
from hatch.plugin.utils import load_plugin_from_script


class CustomEnvironmentCollector:
    PLUGIN_NAME = 'custom'

    def __new__(  # type: ignore
        cls,
        root: str,
        config: dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> EnvironmentCollectorInterface:
        custom_script = config.get('path', DEFAULT_CUSTOM_SCRIPT)
        if not isinstance(custom_script, str):
            message = f'Option `path` for environment collector `{cls.PLUGIN_NAME}` must be a string'
            raise TypeError(message)

        if not custom_script:
            message = f'Option `path` for environment collector `{cls.PLUGIN_NAME}` must not be empty if defined'
            raise ValueError(message)

        path = os.path.normpath(os.path.join(root, custom_script))
        if not os.path.isfile(path):
            message = f'Plugin script does not exist: {custom_script}'
            raise OSError(message)

        hook_class = load_plugin_from_script(
            path, custom_script, EnvironmentCollectorInterface, 'environment_collector'
        )
        hook = hook_class(root, config, *args, **kwargs)

        # Always keep the name to avoid confusion
        hook.PLUGIN_NAME = cls.PLUGIN_NAME

        return hook
