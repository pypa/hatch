# Plugins

-----

Hatch uses Python entrypoints for plugin discovery, making it easy to extend functionality.

## Overview

All plugins are classes that inherit from a particular [type](#types) interface and define a `PLUGIN_NAME` attribute.

Plugin registration is done through dedicated entrypoint groups. For example, to create a custom environment:

```python tab="my_package/environment.py"
from hatch.env.plugin.interface import EnvironmentInterface


class SpecialEnvironment(EnvironmentInterface):
    PLUGIN_NAME = 'special'

    # Your implementation here
    ...
```

```toml tab="pyproject.toml"
[project.entry-points."hatch.environment"]
special = "my_package.environment:SpecialEnvironment"
```

!!! note "Legacy hook-based registration"
    Previous versions of Hatch used pluggy hooks for plugin registration. This approach is **deprecated** but still supported for backward compatibility. See [Legacy Plugin Registration](#legacy-plugin-registration) below for migration guidance.

## Project configuration

### Naming

It is recommended that plugin project names are prefixed with `hatch-`. For example, if you wanted to make a plugin that provides some functionality for a product named `foo` you might do:

```toml tab="pyproject.toml"
[project]
name = "hatch-foo"
```

### Discovery

Define your plugin using the appropriate entrypoint group for its type:

```toml tab="pyproject.toml"
[project.entry-points."hatch.builder"]
foo = "hatch_foo.builder:FooBuilder"

[project.entry-points."hatch.environment"]
foo = "hatch_foo.environment:FooEnvironment"
```

The entrypoint name can be anything, but using your plugin's `PLUGIN_NAME` is recommended for clarity. The path should point directly to your plugin class using the format `module.path:ClassName`.

#### Entrypoint Groups

Use these entrypoint groups based on your plugin type:

| Plugin Type | Entrypoint Group | Used By |
|------------|------------------|---------|
| Builder | `hatch.builder` | Hatchling |
| Build Hook | `hatch.build_hook` | Hatchling |
| Metadata Hook | `hatch.metadata_hook` | Hatchling |
| Version Source | `hatch.version_source` | Hatchling |
| Version Scheme | `hatch.version_scheme` | Hatchling/Hatch |
| Environment | `hatch.environment` | Hatch |
| Environment Collector | `hatch.environment_collector` | Hatch |
| Publisher | `hatch.publisher` | Hatch |
| Template | `hatch.template` | Hatch |

### Classifier

Add [`Framework :: Hatch`](https://pypi.org/search/?c=Framework+%3A%3A+Hatch) to your project's [classifiers](../config/metadata.md#classifiers) to make it easy to search for Hatch plugins:

```toml tab="pyproject.toml"
[project]
classifiers = [
  ...
  "Framework :: Hatch",
  ...
]
```

## Types

### Hatchling

These are all involved in building projects and therefore any defined dependencies are automatically installed in each build environment.

- [Builder](builder/reference.md)
- [Build hook](build-hook/reference.md)
- [Metadata hook](metadata-hook/reference.md)
- [Version source](version-source/reference.md)
- [Version scheme](version-scheme/reference.md)

### Hatch

These must be installed in the same environment as Hatch itself.

- [Environment](environment/reference.md)
- [Environment collector](environment-collector/reference.md)
- [Publisher](publisher/reference.md)

## Legacy Plugin Registration

!!! warning "Deprecated"
    This section describes the old hook-based plugin registration system. It is **deprecated** and will emit warnings when used. Please migrate to direct entrypoint groups as described above.

### Old Method (Deprecated)

Previously, plugins were registered through the `hatch` entrypoint group pointing to a hooks module:

```toml tab="pyproject.toml"
[project.entry-points.hatch]
foo = "pkg.hooks"
```

```python tab="pkg/hooks.py"
from hatchling.plugin import hookimpl

from .plugin import FooBuilder


@hookimpl
def hatch_register_builder():
    return FooBuilder
```

### Migration Guide

To migrate from the old hook-based system to direct entrypoints:

1. **Remove the hooks module** - Delete your `hooks.py` file containing `@hookimpl` decorated functions

2. **Update entrypoints** - Change from the generic `hatch` group to specific groups:

```toml tab="Before"
[project.entry-points.hatch]
foo = "pkg.hooks"
```

```toml tab="After"
[project.entry-points."hatch.builder"]
foo = "pkg.plugin:FooBuilder"
```

3. **Point directly to classes** - Instead of a hooks module, point directly to your plugin class using `module.path:ClassName` format

4. **Update documentation** - If you have plugin documentation, update examples to show the new entrypoint approach

The old system will continue to work with deprecation warnings to give plugin authors time to migrate.
