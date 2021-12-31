# Build hook plugins

-----

A build hook provides code that will be executed at various stages of the build process. See the documentation for [build hook configuration](../config/build.md#build-hooks).

## Known third-party

- [hatch-mypyc](https://github.com/ofek/hatch-mypyc) - compiles code with [Mypyc](https://github.com/mypyc/mypyc)

## Overview

Build hooks run for every selected [version](../config/build.md#versions) of build targets.

The [initialization](#hatchling.builders.hooks.plugin.interface.BuildHookInterface.initialize) stage occurs immediately before each build and the [finalization](#hatchling.builders.hooks.plugin.interface.BuildHookInterface.finalize) stage occurs immediately after. Each stage has the opportunity to view or modify [build data](#build-data).

## Build data

Build data is a simple mapping whose contents can influence the behavior of builds. Which fields are recognized depends on each build target.

The following fields are always present and recognized by the build system itself:

| Field | Type | Description |
| --- | --- | --- |
| `artifacts` | `#!python list[str]` | This is a list of extra paths to [artifacts](../config/build.md#artifacts) and should generally only be appended to |

## Built-in

### Custom

This is a custom class in a given Python file that inherits from the [BuildHookInterface](#hatchling.builders.hooks.plugin.interface.BuildHookInterface).

#### Configuration

The build hook plugin name is `custom`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.hooks.custom]
    [tool.hatch.build.targets.<TARGET_NAME>.hooks.custom]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.hooks.custom]
    [build.targets.<TARGET_NAME>.hooks.custom]
    ```

An option `path` is used to specify the path of the Python file, defaulting to `build.py`.

#### Example

=== ":octicons-file-code-16: build.py"

    ```python
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface


    class CustomBuildHook(BuildHookInterface):
        ...
    ```

If multiple subclasses are found, you must define a function named `get_build_hook` that returns the desired build hook.

!!! note
    Any defined [PLUGIN_NAME](#hatchling.builders.hooks.plugin.interface.BuildHookInterface.PLUGIN_NAME) is ignored and will always be `custom`.

::: hatchling.builders.hooks.plugin.interface.BuildHookInterface
    selection:
      members:
      - PLUGIN_NAME
      - app
      - root
      - config
      - build_config
      - target_name
      - directory
      - clean
      - initialize
      - finalize
