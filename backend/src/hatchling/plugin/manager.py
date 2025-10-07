from __future__ import annotations

from typing import TypeVar

from hatchling.plugin.finder import PluginFinder


class PluginManager:
    """
    Plugin registry that uses PluginFinder for entrypoint-based discovery.

    This replaces the old pluggy-based PluginManager while maintaining
    the same public API for backward compatibility.
    """

    def __init__(self) -> None:
        self.finder = PluginFinder()
        self._cached_registers: dict[str, ClassRegister] = {}

    def __getattr__(self, name: str) -> ClassRegister:
        """
        Dynamically create ClassRegister for plugin types on first access.

        Example: plugin_manager.builder returns a ClassRegister for builders.
        """
        if name.startswith("_"):
            msg = f"'{type(self).__name__}' object has no attribute '{name}'"
            raise AttributeError(msg)

        if name not in self._cached_registers:
            register = ClassRegister(self.finder, name)
            self._cached_registers[name] = register

        return self._cached_registers[name]


class ClassRegister:
    """
    Provides access to plugins of a specific type.

    Maintains the same API as the old ClassRegister for compatibility.
    """

    def __init__(self, finder: PluginFinder, plugin_type: str) -> None:
        self.finder = finder
        self.plugin_type = plugin_type
        self._cached_plugins: dict[str, type] | None = None

    def collect(self, *, include_third_party: bool = True) -> dict[str, type]:  # noqa: ARG002
        """
        Collect all plugins of this type.

        Args:
            include_third_party: Currently ignored (always loads all plugins).
                                 Kept for API compatibility.

        Returns:
            Dictionary mapping plugin names to plugin classes.
        """
        # For the new system, we always load all plugins at once
        # The include_third_party parameter is kept for API compatibility
        if self._cached_plugins is None:
            self._cached_plugins = self.finder.find_plugins(self.plugin_type)

        return self._cached_plugins.copy()

    def get(self, name: str) -> type | None:
        """
        Get a specific plugin by name.

        Args:
            name: The plugin name (from PLUGIN_NAME attribute).

        Returns:
            The plugin class, or None if not found.
        """
        return self.collect().get(name)


PluginManagerBound = TypeVar("PluginManagerBound", bound=PluginManager)
