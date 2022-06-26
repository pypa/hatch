# Build hook plugins

-----

A build hook provides code that will be executed at various stages of the build process. See the documentation for [build hook configuration](../config/build.md#build-hooks).

## Known third-party

- [hatch-mypyc](https://github.com/ofek/hatch-mypyc) - compiles code with [Mypyc](https://github.com/mypyc/mypyc)

## Overview

Build hooks run for every selected [version](../config/build.md#versions) of build targets.

The [initialization](#hatchling.builders.hooks.plugin.interface.BuildHookInterface.initialize) stage occurs immediately before each build and the [finalization](#hatchling.builders.hooks.plugin.interface.BuildHookInterface.finalize) stage occurs immediately after. Each stage has the opportunity to view or modify [build data](#build-data).

## Build data

Build data is a simple mapping whose contents can influence the behavior of builds. Which fields exist and are recognized depends on each build target.

The following fields are always present and recognized by the build system itself:

| Field | Type | Description |
| --- | --- | --- |
| `artifacts` | `#!python list[str]` | This is a list of extra paths to [artifacts](../config/build.md#artifacts) and should generally only be appended to |
| `force_include` | `#!python dict[str, str]` | This is a mapping of extra [explicit paths](../config/build.md#explicit-selection), with this mapping taking precedence in case of conflicts |
| `build_hooks` | `#!python tuple[str, ...]` | This is an immutable sequence of the names of the configured build hooks and matches the order in which they run |

!!! attention
    While user-facing TOML options are hyphenated, build data fields should be named with underscores to allow plugins to use them as valid Python identifiers.

## Built-in

### Version

This is a custom class in a given Python file that inherits from the [BuildHookInterface](#hatchling.builders.hooks.plugin.interface.BuildHookInterface).

#### Configuration

The build hook plugin name is `version`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.hooks.version]
    [tool.hatch.build.targets.<TARGET_NAME>.hooks.version]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.hooks.version]
    [build.targets.<TARGET_NAME>.hooks.version]
    ```

##### Options

| Option | Description |
| --- | --- |
| `path` (required) | A relative path to the desired file |
| `template` | A string representing the entire contents of `path` that will be formatted with a `version` variable |
| `pattern` | Rather than updating the entire file, a regular expression may be used that has a named group called `version` that represents the version. If set to `true`, a pattern will be used that looks for a variable named `__version__` or `VERSION` that is set to a string containing the version, optionally prefixed with the lowercase letter `v`. |

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

##### Options

| Option | Default | Description |
| --- | --- | --- |
| `path` | `hatch_build.py` | The path of the Python file |

#### Example

=== ":octicons-file-code-16: hatch_build.py"

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
