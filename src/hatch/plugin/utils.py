from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface


def load_plugin_from_script(
    path: str, script_name: str, plugin_class: type[EnvironmentCollectorInterface], plugin_id: str
) -> type[EnvironmentCollectorInterface]:
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location(script_name, path)
    module = module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(module)  # type: ignore

    plugin_finder = f'get_{plugin_id}'
    names = dir(module)
    if plugin_finder in names:
        return getattr(module, plugin_finder)()

    subclasses = []
    for name in names:
        obj = getattr(module, name)
        if obj is plugin_class:
            continue

        try:
            if issubclass(obj, plugin_class):
                subclasses.append(obj)
        except TypeError:
            continue

    if not subclasses:
        message = f'Unable to find a subclass of `{plugin_class.__name__}` in `{script_name}`: {path}'
        raise ValueError(message)

    if len(subclasses) > 1:
        message = (
            f'Multiple subclasses of `{plugin_class.__name__}` found in `{script_name}`, '
            f'select one by defining a function named `{plugin_finder}`: {path}'
        )
        raise ValueError(message)

    return subclasses[0]
