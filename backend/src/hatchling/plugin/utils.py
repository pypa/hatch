def load_plugin_from_script(path, script_name, plugin_class, plugin_id):
    import importlib

    spec = importlib.util.spec_from_file_location(script_name, path)
    module = importlib.util.module_from_spec(spec)
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
        raise ValueError(f'Unable to find a subclass of `{plugin_class.__name__}` in `{script_name}`: {path}')
    elif len(subclasses) > 1:
        raise ValueError(
            f'Multiple subclasses of `{plugin_class.__name__}` found in `{script_name}`, '
            f'select one by defining a function named `{plugin_finder}`: {path}'
        )
    else:
        return subclasses[0]
