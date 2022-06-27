# Build hook plugins

-----

A build hook provides code that will be executed at various stages of the build process. See the documentation for [build hook configuration](../../config/build.md#build-hooks).

## Known third-party

- [hatch-mypyc](https://github.com/ofek/hatch-mypyc) - compiles code with [Mypyc](https://github.com/mypyc/mypyc)

## Overview

Build hooks run for every selected [version](../../config/build.md#versions) of build targets.

The [initialization](#hatchling.builders.hooks.plugin.interface.BuildHookInterface.initialize) stage occurs immediately before each build and the [finalization](#hatchling.builders.hooks.plugin.interface.BuildHookInterface.finalize) stage occurs immediately after. Each stage has the opportunity to view or modify [build data](#build-data).

## Build data

Build data is a simple mapping whose contents can influence the behavior of builds. Which fields exist and are recognized depends on each build target.

The following fields are always present and recognized by the build system itself:

| Field | Type | Description |
| --- | --- | --- |
| `artifacts` | `#!python list[str]` | This is a list of extra paths to [artifacts](../../config/build.md#artifacts) and should generally only be appended to |
| `force_include` | `#!python dict[str, str]` | This is a mapping of extra [explicit paths](../../config/build.md#explicit-selection), with this mapping taking precedence in case of conflicts |
| `build_hooks` | `#!python tuple[str, ...]` | This is an immutable sequence of the names of the configured build hooks and matches the order in which they run |

!!! attention
    While user-facing TOML options are hyphenated, build data fields should be named with underscores to allow plugins to use them as valid Python identifiers.

## Built-in

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
