from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from hatchling.metadata.plugin.interface import MetadataHookInterface
from hatchling.plugin.utils import load_plugin_from_script
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT

if TYPE_CHECKING:
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomMetadataHook:
    PLUGIN_NAME = 'custom'

    def __new__(cls, root: str, config: dict[str, Any], *args: Any, **kwargs: Any) -> BuildHookInterface:
        build_script = config.get('path', DEFAULT_BUILD_SCRIPT)
        if not isinstance(build_script, str):
            raise TypeError(f'Option `path` for metadata hook `{cls.PLUGIN_NAME}` must be a string')
        elif not build_script:
            raise ValueError(f'Option `path` for metadata hook `{cls.PLUGIN_NAME}` must not be empty if defined')

        path = os.path.normpath(os.path.join(root, build_script))
        if not os.path.isfile(path):
            raise OSError(f'Build script does not exist: {build_script}')

        hook_class = load_plugin_from_script(path, build_script, MetadataHookInterface, 'metadata_hook')
        hook = hook_class(root, config, *args, **kwargs)

        # Always keep the name to avoid confusion
        hook.PLUGIN_NAME = cls.PLUGIN_NAME

        return hook
