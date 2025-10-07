from hatchling.plugin.manager import PluginManager as _PluginManager


class PluginManager(_PluginManager):
    """
    Hatch-specific plugin manager.

    Inherits from hatchling's PluginManager and adds support for
    hatch-specific plugin types (environment, publisher, template, etc.).

    The new implementation uses PluginFinder directly via entrypoints,
    removing the need for hook registration methods.
    """

    pass
