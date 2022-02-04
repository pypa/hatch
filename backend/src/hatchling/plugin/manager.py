from collections import OrderedDict

import pluggy


class PluginManager(object):
    def __init__(self):
        self.manager = pluggy.PluginManager('hatch')
        self.third_party_plugins = ThirdPartyPlugins(self.manager)
        self.initialized = False

    def initialize(self):
        from . import specs

        self.manager.add_hookspecs(specs)

    def __getattr__(self, name):
        if not self.initialized:
            self.initialize()
            self.initialized = True

        hook_name = 'hatch_register_{}'.format(name)
        getattr(self, hook_name, None)()

        register = ClassRegister(getattr(self.manager.hook, hook_name), 'PLUGIN_NAME', self.third_party_plugins)
        setattr(self, name, register)
        return register

    def hatch_register_version_source(self):
        from ..version.source.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_builder(self):
        from ..builders.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_build_hook(self):
        from ..builders.hooks.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_metadata_hook(self):
        from ..metadata.plugin import hooks

        self.manager.register(hooks)


class ClassRegister:
    def __init__(self, registration_method, identifier, third_party_plugins):
        self.registration_method = registration_method
        self.identifier = identifier
        self.third_party_plugins = third_party_plugins

    def collect(self, include_third_party=True):
        if include_third_party and not self.third_party_plugins.loaded:
            self.third_party_plugins.load()

        classes = OrderedDict()

        for registered_classes in self.registration_method():
            if not isinstance(registered_classes, list):
                registered_classes = [registered_classes]

            for registered_class in registered_classes:
                name = getattr(registered_class, self.identifier, None)
                if not name:  # no cov
                    raise ValueError('Class `{}` does not have a {} attribute.'.format(registered_class.__name__, name))
                elif name in classes:  # no cov
                    raise ValueError(
                        'Class `{}` defines its name as `{}` but that name is already used by '
                        '`{}`.'.format(registered_class.__name__, name, classes[name].__name__)
                    )

                classes[name] = registered_class

        return classes

    def get(self, name):
        if not self.third_party_plugins.loaded:
            classes = self.collect(include_third_party=False)
            if name in classes:
                return classes[name]

        return self.collect().get(name)


class ThirdPartyPlugins(object):
    def __init__(self, manager):
        self.manager = manager
        self.loaded = False

    def load(self):
        self.manager.load_setuptools_entrypoints('hatch')
        self.loaded = True
