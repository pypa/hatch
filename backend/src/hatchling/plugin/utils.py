from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface
    from hatchling.builders.plugin.interface import BuilderInterface
    from hatchling.metadata.plugin.interface import MetadataHookInterface

    T = TypeVar('T', BuilderInterface, BuildHookInterface, MetadataHookInterface)


def load_plugin_from_script(path: str, script_name: str, plugin_class: type[T], plugin_id: str) -> type[T]:
    import importlib

    spec = importlib.util.spec_from_file_location(script_name, path)  # type: ignore
    module = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(module)

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
    elif len(subclasses) > 1:
        message = (
            f'Multiple subclasses of `{plugin_class.__name__}` found in `{script_name}`, '
            f'select one by defining a function named `{plugin_finder}`: {path}'
        )
        raise ValueError(message)
    else:
        return subclasses[0]
