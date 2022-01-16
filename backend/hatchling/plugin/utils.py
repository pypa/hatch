import sys

if sys.version_info[0] >= 3:

    def load_plugin_from_script(path, script_name, plugin_class, plugin_id):
        import importlib

        spec = importlib.util.spec_from_file_location(script_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        plugin_finder = 'get_{}'.format(plugin_id)
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
            raise ValueError(
                'Unable to find a subclass of `{}` in `{}`: {}'.format(plugin_class.__name__, script_name, path)
            )
        elif len(subclasses) > 1:
            raise ValueError(
                'Multiple subclasses of `{}` found in `{}`, select one by defining a function named `{}`: {}'.format(
                    plugin_class.__name__, script_name, plugin_finder, path
                )
            )
        else:
            return subclasses[0]

else:  # no cov

    def load_plugin_from_script(path, script_name, plugin_class, plugin_id):
        from io import open

        with open(path, 'r', encoding='utf-8') as f:
            compiled = compile(f.read(), filename=script_name, mode='exec')

        local_variables = {}
        exec(compiled, globals(), local_variables)

        plugin_finder = 'get_{}'.format(plugin_id)
        if plugin_finder in local_variables:
            return local_variables[plugin_finder]()

        subclasses = []
        for obj in local_variables.values():
            if obj is plugin_class:
                continue

            try:
                if issubclass(obj, plugin_class):
                    subclasses.append(obj)
            except TypeError:
                continue

        if not subclasses:
            raise ValueError(
                'Unable to find a subclass of `{}` in `{}`: {}'.format(plugin_class.__name__, script_name, path)
            )
        elif len(subclasses) > 1:
            raise ValueError(
                'Multiple subclasses of `{}` found in `{}`, select one by defining a function named `{}`: {}'.format(
                    plugin_class.__name__, script_name, plugin_finder, path
                )
            )
        else:
            return subclasses[0]
