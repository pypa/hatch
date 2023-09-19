from types import ModuleType
from typing import Iterator

from hatchling.plugin.manager import PluginManager as _PluginManager
from hatchling.plugin.manager import DeferredClassRegister

class PluginManager(_PluginManager):
    def get_specs(self) -> Iterator[ModuleType]:
        yield from super().get_specs()

        from hatch.plugin import specs

        yield specs

    @DeferredClassRegister
    def environment(self):
        from hatch.env.plugin import hooks
        return hooks

    @DeferredClassRegister
    def environment_collector(self):
        from hatch.env.collectors.plugin import hooks
        return hooks

    @DeferredClassRegister
    def publisher(self):
        from hatch.publish.plugin import hooks
        return hooks

    @DeferredClassRegister
    def template(self):
        from hatch.template.plugin import hooks
        return hooks
