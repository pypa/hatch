from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    # Python 3.9 - entry_points() returns a dict-like object, not a function with group param
    from importlib.metadata import entry_points as _entry_points

    def entry_points(*, group: str):
        """Wrapper for Python 3.9 compatibility."""
        eps = _entry_points()
        return eps.get(group, [])


if TYPE_CHECKING:
    pass


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

# Built-in plugins for hatchling (used as fallback during development/bootstrap)
BUILTIN_PLUGINS = {
    "version_source": {
        "code": "hatchling.version.source.code:CodeSource",
        "env": "hatchling.version.source.env:EnvSource",
        "regex": "hatchling.version.source.regex:RegexSource",
    },
    "version_scheme": {
        "standard": "hatchling.version.scheme.standard:StandardScheme",
    },
    "builder": {
        "app": "hatchling.builders.app:AppBuilder",
        "binary": "hatchling.builders.binary:BinaryBuilder",
        "custom": "hatchling.builders.custom:CustomBuilder",
        "sdist": "hatchling.builders.sdist:SdistBuilder",
        "wheel": "hatchling.builders.wheel:WheelBuilder",
    },
    "build_hook": {
        "custom": "hatchling.builders.hooks.custom:CustomBuildHook",
        "version": "hatchling.builders.hooks.version:VersionBuildHook",
    },
    "metadata_hook": {
        "custom": "hatchling.metadata.custom:CustomMetadataHook",
    },
    "environment": {
        "system": "hatch.env.system:SystemEnvironment",
        "virtual": "hatch.env.virtual:VirtualEnvironment",
    },
    "environment_collector": {
        "custom": "hatch.env.collectors.custom:CustomEnvironmentCollector",
        "default": "hatch.env.collectors.default:DefaultEnvironmentCollector",
    },
    "publisher": {
        "index": "hatch.publish.index:IndexPublisher",
    },
    "template": {
        "default": "hatch.template.default:DefaultTemplate",
    },
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

        # If no plugins found via entrypoints, try loading built-in plugins directly
        # This handles development/bootstrap scenarios where entrypoints aren't installed yet
        if not plugins and plugin_type in BUILTIN_PLUGINS:
            builtin_specs = BUILTIN_PLUGINS[plugin_type]
            for plugin_name, module_path in builtin_specs.items():
                # Built-in plugins should always be available; if not, let the error propagate
                plugin_class = self._load_class_from_path(module_path)
                plugins[plugin_name] = plugin_class

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

    @staticmethod
    def _load_class_from_path(class_path: str) -> type:
        """
        Load a class from a module:class path string.

        Args:
            class_path: Path in format "module.path:ClassName"

        Returns:
            The loaded class
        """
        module_path, class_name = class_path.split(":")
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)

    @staticmethod
    def _load_from_entrypoint_group(group_name: str) -> dict[str, type]:
        """Load plugins from a direct entrypoint group."""
        plugins: dict[str, type] = {}

        eps = entry_points(group=group_name)

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

            except Exception as e:  # noqa: BLE001
                warnings.warn(
                    f"Failed to load plugin from entrypoint '{ep.name}' in group '{group_name}': {e}",
                    UserWarning,
                    stacklevel=3,
                )

        return plugins

    @staticmethod
    def _load_legacy_plugins(plugin_type: str) -> dict[str, type]:
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

        eps = entry_points(group="hatch")

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

            except Exception as e:  # noqa: BLE001
                warnings.warn(
                    f"Failed to load legacy plugin from entrypoint '{ep.name}' in 'hatch' group: {e}",
                    UserWarning,
                    stacklevel=4,
                )

        return plugins
