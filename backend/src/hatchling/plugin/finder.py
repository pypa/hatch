from __future__ import annotations

import sys
import warnings
from pathlib import Path
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


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

if TYPE_CHECKING:
    pass


def _load_builtin_plugins_from_pyproject() -> dict[str, dict[str, str]]:
    """
    Load built-in plugin definitions from pyproject.toml files.

    This reads the entrypoint definitions directly from the source pyproject.toml
    files to avoid duplicating plugin registration data.

    Returns:
        Dictionary mapping plugin types to their plugin definitions
    """
    builtin_plugins: dict[str, dict[str, str]] = {}

    # Find the pyproject.toml files
    # They should be in the parent directories of this file
    finder_path = Path(__file__).resolve()

    # Try hatchling's pyproject.toml (backend/pyproject.toml)
    hatchling_pyproject = finder_path.parents[3] / "pyproject.toml"

    # Try hatch's pyproject.toml (../../pyproject.toml from hatchling)
    hatch_pyproject = hatchling_pyproject.parent.parent / "pyproject.toml"

    for pyproject_path in [hatchling_pyproject, hatch_pyproject]:
        if not pyproject_path.exists():
            continue

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            # Extract entry-points
            entrypoints = data.get("project", {}).get("entry-points", {})

            # Look for hatch.* groups
            for group_name, plugins in entrypoints.items():
                if group_name.startswith("hatch."):
                    plugin_type = group_name.removeprefix("hatch.")
                    if plugin_type not in builtin_plugins:
                        builtin_plugins[plugin_type] = {}
                    builtin_plugins[plugin_type].update(plugins)

        except Exception:  # noqa: BLE001, S110
            # If we can't read the pyproject.toml, continue without it
            # This shouldn't happen in normal operation, but we don't want to break
            # if the file structure changes
            pass

    return builtin_plugins


class PluginFinder:
    """
    Discovers and loads plugins using a two-tier approach:
    1. Primary: Direct entrypoint groups (e.g., 'hatch.builder')
    2. Fallback: Legacy 'hatch' group with hook functions (deprecated)
    """

    def __init__(self) -> None:
        self._legacy_plugins_checked = False
        self._has_legacy_plugins = False
        self._builtin_plugins: dict[str, dict[str, str]] | None = None

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
        if not plugins:
            if self._builtin_plugins is None:
                self._builtin_plugins = _load_builtin_plugins_from_pyproject()

            if plugin_type in self._builtin_plugins:
                builtin_specs = self._builtin_plugins[plugin_type]
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
        # Hook name follows pattern: hatch_register_{plugin_type}
        hook_name = f"hatch_register_{plugin_type}"

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
