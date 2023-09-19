from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from types import ModuleType
from typing import Callable, TypeVar, Generator

import pluggy

PluginBaseClass = TypeVar('PluginBaseClass')

@dataclass
class DeferredClassRegister:

    name: str
    _load_hooks: Callable[[PluginmanagerBound], ModuleType] = field(repr=False)
    def __init__(self, load_hooks: Callable[[PluginmanagerBound], ModuleType]) -> None:
        self._load_hooks = load_hooks

    def __set_name__(self, owner: type[PluginManagerBound], name: str):
        self._name = name

    def __get__(self, instance: PluginManagerBound, owner: type[PluginManagerBound]) -> ClassRegister:
        if instance is None:
            return self
        else:
            hook_name = f'hatch_register_{self._name}'
            hook_module = self._load_hooks(instance)
            instance.manager.register(hook_module)

            register = ClassRegister(getattr(instance.manager.hook, hook_name), 'PLUGIN_NAME', instance.third_party_plugins)
            setattr(instance, self._name, register)
            return register

class PluginManager:


    @cached_property
    def third_party_plugins(self) -> ThirdPartyPlugins:
        return ThirdPartyPlugins(self.manager)

    @cached_property
    def manager(self) -> pluggy.PluginManager:
        pm = pluggy.PluginManager('hatch')
        for spec in self.get_specs():
            pm.add_hookspecs(spec)
        return pm

    def get_specs(self) -> Generator[ModuleType]:
        from hatchling.plugin import specs
        yield specs


    @DeferredClassRegister
    def version_source(self) -> None:
        from hatchling.version.source.plugin import hooks
        return hooks

    @DeferredClassRegister
    def version_scheme(self) -> ModuleType:
        from hatchling.version.scheme.plugin import hooks
        return hooks

    @DeferredClassRegister
    def builder(self) -> ModuleType:
        from hatchling.builders.plugin import hooks
        return hooks

    @DeferredClassRegister
    def build_hook(self) -> ModuleType:
        from hatchling.builders.hooks.plugin import hooks
        return hooks

    @DeferredClassRegister
    def metadata_hook(self) -> ModuleType:
        from hatchling.metadata.plugin import hooks

        return hooks


class ClassRegister():
    def __init__(self, registration_method: Callable, identifier: str, third_party_plugins: ThirdPartyPlugins) -> None:
        self.registration_method = registration_method
        self.identifier = identifier
        self.third_party_plugins = third_party_plugins

    def collect(self, *, include_third_party: bool = True) -> dict:
        if include_third_party :
            self.third_party_plugins.ensure_loaded()

        classes: dict[str, type] = {}

        for registered_classes in self.registration_method():
            if not isinstance(registered_classes, list):
                registered_classes = [registered_classes]

            for registered_class in registered_classes:
                name = getattr(registered_class, self.identifier, None)
                if not name:  # no cov
                    message = f'Class `{registered_class.__name__}` does not have a {name} attribute.'
                    raise ValueError(message)
                elif name in classes:  # no cov
                    message = (
                        f'Class `{registered_class.__name__}` defines its name as `{name}` but '
                        f'that name is already used by `{classes[name].__name__}`.'
                    )
                    raise ValueError(message)

                classes[name] = registered_class

        return classes

    def get(self, name: str) -> type | None:
        if not self.third_party_plugins.loaded:
            classes = self.collect(include_third_party=False)
            if name in classes:
                return classes[name]

        return self.collect().get(name)


@dataclass
class ThirdPartyPlugins:

    manager: pluggy.PluginManager
    loaded: bool = False

    def ensure_loaded(self) -> None:
        if not self.loaded:
            self.manager.load_setuptools_entrypoints('hatch')
            self.loaded = True


PluginManagerBound = TypeVar('PluginManagerBound', bound=PluginManager)
