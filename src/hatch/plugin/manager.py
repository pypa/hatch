from hatchling.plugin.manager import PluginManager as _PluginManager


class PluginManager(_PluginManager):
    def initialize(self) -> None:
        super().initialize()

        from hatch.plugin import specs

        self.manager.add_hookspecs(specs)

    def hatch_register_environment(self) -> None:
        from hatch.env.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_environment_collector(self) -> None:
        from hatch.env.collectors.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_publisher(self) -> None:
        from hatch.publish.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_template(self) -> None:
        from hatch.template.plugin import hooks

        self.manager.register(hooks)
