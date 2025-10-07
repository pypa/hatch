from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points

if TYPE_CHECKING:
    from typing import Any


# Mapping from plugin type names to their hook function names (for legacy support)
HOOK_NAME_MAPPING = {
    "version_source": "hatch_register_version_source",
    "version_scheme": "hatch_register_version_scheme",
    "builder": "hatch_register_builder",
    "build_hook": "hatch_register_build_hook",
    "metadata_hook": "hatch_register_metadata_hook",
    "environment": "hatch_register_environment",
    "environment_collector": "hatch_register_environment_collector",
    "publisher": "hatch_register_publisher",
    "template": "hatch_register_template",
}


class PluginFinder:
    """
    Discovers and loads plugins using a two-tier approach:
    1. Primary: Direct entrypoint groups (e.g., 'hatch.builder')
    2. Fallback: Legacy 'hatch' group with hook functions (deprecated)
    """

    def __init__(self) -> None:
        self._legacy_plugins_checked = False
        self._has_legacy_plugins = False

    def find_plugins(self, plugin_type: str) -> dict[str, type]:
        """
        Find all plugins of a given type.

        Args:
            plugin_type: The plugin type (e.g., 'builder', 'version_source')

        Returns:
            Dictionary mapping plugin names to plugin classes
        """
        plugins: dict[str, type] = {}

        # Primary path: Load from new entrypoint groups
        group_name = f"hatch.{plugin_type}"
        new_style_plugins = self._load_from_entrypoint_group(group_name)
        plugins.update(new_style_plugins)

        # Fallback path: Load from legacy 'hatch' group
        legacy_plugins = self._load_legacy_plugins(plugin_type)
        if legacy_plugins:
            if not self._has_legacy_plugins:
                self._has_legacy_plugins = True
                warnings.warn(
                    "Legacy plugin registration via 'hatch' entrypoint group and @hookimpl is deprecated. "
                    f"Please migrate to direct entrypoint groups like '{group_name}'. "
                    "See https://hatch.pypa.io/latest/plugins/about/ for migration guide.",
                    DeprecationWarning,
                    stacklevel=2,
                )

            # Legacy plugins don't override new-style plugins
            for name, cls in legacy_plugins.items():
                if name not in plugins:
                    plugins[name] = cls

        return plugins

    def _load_from_entrypoint_group(self, group_name: str) -> dict[str, type]:
        """Load plugins from a direct entrypoint group."""
        plugins: dict[str, type] = {}

        try:
            eps = entry_points(group=group_name)
        except TypeError:
            # Python 3.9 compatibility
            eps = entry_points().get(group_name, [])

        for ep in eps:
            try:
                plugin_class = ep.load()
                plugin_name = getattr(plugin_class, "PLUGIN_NAME", None)

                if not plugin_name:
                    warnings.warn(
                        f"Plugin class '{plugin_class.__name__}' from entrypoint '{ep.name}' "
                        f"in group '{group_name}' does not have a PLUGIN_NAME attribute. Skipping.",
                        UserWarning,
                        stacklevel=3,
                    )
                    continue

                if plugin_name in plugins:
                    warnings.warn(
                        f"Plugin name '{plugin_name}' is already registered in group '{group_name}'. "
                        f"Skipping duplicate from entrypoint '{ep.name}'.",
                        UserWarning,
                        stacklevel=3,
                    )
                    continue

                plugins[plugin_name] = plugin_class

            except Exception as e:
                warnings.warn(
                    f"Failed to load plugin from entrypoint '{ep.name}' in group '{group_name}': {e}",
                    UserWarning,
                    stacklevel=3,
                )

        return plugins

    def _load_legacy_plugins(self, plugin_type: str) -> dict[str, type]:
        """
        Load plugins from legacy 'hatch' entrypoint group.

        This loads modules from the 'hatch' group and directly calls their
        hook functions (e.g., hatch_register_builder) to get plugin classes.
        No PluginManager is needed since hooks are just regular functions.
        """
        plugins: dict[str, type] = {}
        hook_name = HOOK_NAME_MAPPING.get(plugin_type)

        if not hook_name:
            return plugins

        try:
            eps = entry_points(group="hatch")
        except TypeError:
            # Python 3.9 compatibility
            eps = entry_points().get("hatch", [])

        for ep in eps:
            try:
                # Load the module
                module = ep.load()

                # Check if it has the hook function
                hook_func = getattr(module, hook_name, None)
                if not hook_func:
                    continue

                # Call the hook function directly to get plugin class(es)
                result = hook_func()

                # Handle both single class and list of classes
                if result is None:
                    continue

                classes = result if isinstance(result, list) else [result]

                for plugin_class in classes:
                    plugin_name = getattr(plugin_class, "PLUGIN_NAME", None)

                    if not plugin_name:
                        warnings.warn(
                            f"Plugin class '{plugin_class.__name__}' from legacy hook "
                            f"'{hook_name}' in module '{ep.name}' does not have a PLUGIN_NAME attribute. Skipping.",
                            UserWarning,
                            stacklevel=4,
                        )
                        continue

                    if plugin_name in plugins:
                        continue  # Skip duplicates

                    plugins[plugin_name] = plugin_class

            except Exception as e:
                warnings.warn(
                    f"Failed to load legacy plugin from entrypoint '{ep.name}' in 'hatch' group: {e}",
                    UserWarning,
                    stacklevel=4,
                )

        return plugins
