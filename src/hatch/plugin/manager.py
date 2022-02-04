from hatchling.plugin.manager import PluginManager as _PluginManager


class PluginManager(_PluginManager):
    def initialize(self):
        super().initialize()

        from . import specs

        self.manager.add_hookspecs(specs)

    def hatch_register_environment(self):
        from ..env.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_environment_collector(self):
        from ..env.collectors.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_version_scheme(self):
        from ..version.scheme.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_publisher(self):
        from ..publish.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_template(self):
        from ..template.plugin import hooks

        self.manager.register(hooks)
