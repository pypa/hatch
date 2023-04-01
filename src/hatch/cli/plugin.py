from itertools import chain

import pluggy
from click import Group
from hatchling.plugin import specs


def load_plugins(hatch: Group):
    pm = pluggy.PluginManager("hatch")

    pm.add_hookspecs(specs)
    pm.load_setuptools_entrypoints("hatch")

    plugins = pm.hook.hatch_register_commands()
    for plugin in chain.from_iterable(plugins):
        hatch.add_command(plugin)
