# Plugins

-----

Hatch utilizes [pluggy](https://github.com/pytest-dev/pluggy) for its plugin functionality.

## Overview

All plugins provide registration hooks that return one or more classes that inherit from a particular [type](#types) interface.

Each registration hook must be decorated by Hatch's hook marker. For example, if you wanted to create a new kind of environment you could do:

=== ":octicons-file-code-16: hooks.py"

    ```python
    from hatchling.plugin import hookimpl

    from .plugin import SpecialEnvironment


    @hookimpl
    def hatch_register_environment():
        return SpecialEnvironment
    ```

The hooks can return a single class or a list of classes.

Every class must define an attribute called `PLUGIN_NAME` that users will select when they wish to use the plugin. So in the example above, the class might be defined like:

=== ":octicons-file-code-16: plugin.py"

    ```python
    ...
    class SpecialEnvironment(...):
        PLUGIN_NAME = 'special'
        ...
    ```

## Project configuration

### Naming

It is recommended that plugin project names are prefixed with `hatch-`. For example, if you wanted to make a plugin that provides some functionality for a product named `foo` you might do:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project]
    name = "hatch-foo"
    ```

### Discovery

You'll need to define your project as a [Python plugin](../config/metadata.md#plugins) for Hatch:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project.entry-points.hatch]
    foo = "pkg.hooks"
    ```

The name of the plugin should be the project name (excluding any `hatch-` prefix) and the path should represent the module that contains the registration hooks.

## Types

### Hatchling

These are all involved in building projects and therefore any defined dependencies are automatically installed in each build environment.

- [Builder](builder.md)
- [Build hook](build-hook.md)
- [Metadata hook](metadata-hook.md)
- [Version source](version-source.md)

### Hatch

These must be manually installed in the same environment as Hatch itself.

- [Environment](environment.md)
- [Environment collector](environment-collector.md)
- [Publisher](publisher.md)
- [Version scheme](version-scheme.md)
