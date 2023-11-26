from __future__ import annotations

from typing import Callable, TypeVar

import pluggy


class PluginManager:
    def __init__(self) -> None:
        self.manager = pluggy.PluginManager('hatch')
        self.third_party_plugins = ThirdPartyPlugins(self.manager)
        self.initialized = False

    def initialize(self) -> None:
        from hatchling.plugin import specs

        self.manager.add_hookspecs(specs)

    def __getattr__(self, name: str) -> ClassRegister:
        if not self.initialized:
            self.initialize()
            self.initialized = True

        hook_name = f'hatch_register_{name}'
        hook = getattr(self, hook_name, None)
        if hook:
            hook()

        register = ClassRegister(getattr(self.manager.hook, hook_name), 'PLUGIN_NAME', self.third_party_plugins)
        setattr(self, name, register)
        return register

    def hatch_register_version_source(self) -> None:
        from hatchling.version.source.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_version_scheme(self) -> None:
        from hatchling.version.scheme.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_builder(self) -> None:
        from hatchling.builders.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_build_hook(self) -> None:
        from hatchling.builders.hooks.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_metadata_hook(self) -> None:
        from hatchling.metadata.plugin import hooks

        self.manager.register(hooks)


class ClassRegister:
    def __init__(self, registration_method: Callable, identifier: str, third_party_plugins: ThirdPartyPlugins) -> None:
        self.registration_method = registration_method
        self.identifier = identifier
        self.third_party_plugins = third_party_plugins

    def collect(self, *, include_third_party: bool = True) -> dict:
        if include_third_party and not self.third_party_plugins.loaded:
            self.third_party_plugins.load()

        classes: dict[str, type] = {}

        for raw_registered_classes in self.registration_method():
            registered_classes = (
                raw_registered_classes if isinstance(raw_registered_classes, list) else [raw_registered_classes]
            )
            for registered_class in registered_classes:
                name = getattr(registered_class, self.identifier, None)
                if not name:  # no cov
                    message = f'Class `{registered_class.__name__}` does not have a {name} attribute.'
                    raise ValueError(message)

                if name in classes:  # no cov
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


class ThirdPartyPlugins:
    def __init__(self, manager: pluggy.PluginManager) -> None:
        self.manager = manager
        self.loaded = False

    def load(self) -> None:
        self.manager.load_setuptools_entrypoints('hatch')
        self.loaded = True


PluginManagerBound = TypeVar('PluginManagerBound', bound=PluginManager)
