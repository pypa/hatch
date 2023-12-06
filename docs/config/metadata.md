# Project metadata

-----

Project metadata is stored in a `pyproject.toml` file located at the root of a project's tree
and is based entirely on [the standard][project metadata standard].

## Name (*required*) ## {: #name }

The name of the project.

```toml tab="pyproject.toml"
[project]
name = "your-app"
```

## Version (*required*) ## {: #version }

=== ":octicons-file-code-16: pyproject.toml"

    === "Dynamic"
        See the dedicated [versioning](../version.md) section.

        ```toml
        [project]
        ...
        dynamic = ["version"]

        [tool.hatch.version]
        path = "..."
        ```

    === "Static"
        ```toml
        [project]
        ...
        version = "0.0.1"
        ```

## Description

A brief summary of the project.

```toml tab="pyproject.toml"
[project]
...
description = '...'
```

## Readme

The full description of the project.

=== ":octicons-file-code-16: pyproject.toml"

    === "Simple"
        The file extension must be `.md`, `.rst`, or `.txt`.

        ```toml
        [project]
        ...
        readme = "README.md"
        ```

    === "Complex"
        The `content-type` field must be set to `text/markdown`, `text/x-rst`, or `text/plain`.

        === "File"
            A `charset` field may also be set to instruct which encoding to
            use for reading the file, defaulting to `utf-8`.

            ```toml
            [project]
            ...
            readme = {"file" = "README.md", "content-type" = "text/markdown"}
            ```

        === "Text"
            The `content-type` field must be set to `text/markdown` or `text/x-rst`.

            ```toml
            [project]
            ...
            readme = {"text" = "...", "content-type" = "text/markdown"}
            ```

!!! note
    If this is defined as a file, then it will always be included in [source distributions](../plugins/builder/sdist.md) for consistent builds.

## Python support

The Python version requirements of the project.

```toml tab="pyproject.toml"
[project]
...
requires-python = ">=3.8"
```

## License

For more information, see [PEP 639][].

=== ":octicons-file-code-16: pyproject.toml"

    === "SPDX expression"

        ```toml
        [project]
        ...
        license = "Apache-2.0 OR MIT"
        ```

    === "Files"

        === "Paths"

            ```toml
            [project]
            ...
            license-files = { paths = ["LICENSE.txt"] }
            ```

        === "Globs"

            ```toml
            [project]
            ...
            license-files = { globs = ["LICENSES/*"] }
            ```

## Ownership

The people or organizations considered to be the `authors` or `maintainers` of the project.
The exact meaning is open to interpretation; it may list the original or primary authors,
current maintainers, or owners of the package. If the values are the same, prefer only the
use of the `authors` field.

```toml tab="pyproject.toml"
[project]
...
authors = [
  { name = "...", email = "..." },
]
maintainers = [
  { name = "...", email = "..." },
]
```

## Keywords

The keywords used to assist in the discovery of the project.

```toml tab="pyproject.toml"
[project]
...
keywords = [
  "...",
]
```

## Classifiers

The [trove classifiers](https://pypi.org/classifiers/) that apply to the project.

```toml tab="pyproject.toml"
[project]
...
classifiers = [
  "...",
]
```

## URLs

A table of URLs where the key is the URL label and the value is the URL itself.

```toml tab="pyproject.toml"
[project.urls]
Documentation = "..."
"Source code" = "..."
```

## Dependencies

See the [dependency specification](dependency.md) page for more information.

Entries support [context formatting](context.md) and [disallow direct references](#allowing-direct-references) by default.

### Required

```toml tab="pyproject.toml"
[project]
...
dependencies = [
  "...",
]
```

### Optional

```toml tab="pyproject.toml"
[project.optional-dependencies]
option1 = [
  "...",
]
option2 = [
  "...",
]
```

## Entry points

[Entry points](https://packaging.python.org/specifications/entry-points/) are a mechanism for
the project to advertise components it provides to be discovered and used by other code.

### CLI

After installing projects that define CLI scripts, each key will be available along your `PATH` as a command that will call its associated object.

```toml tab="pyproject.toml"
[project.scripts]
cli-name = "pkg.subpkg:func"
```

Using the above example, running `cli-name` would essentially execute the following Python script:

```python
import sys

from pkg.subpkg import func

sys.exit(func())
```

### GUI

GUI scripts are exactly the same as CLI scripts except on Windows, where they are handled specially so that they can be started without a console.

```toml tab="pyproject.toml"
[project.gui-scripts]
gui-name = "pkg.subpkg:func"
```

### Plugins

```toml tab="pyproject.toml"
[project.entry-points.plugin-namespace]
plugin-name1 = "pkg.subpkg1"
plugin-name2 = "pkg.subpkg2:func"
```

## Dynamic

If any metadata fields are set dynamically, like the [`version`](#version) may be, then they must be listed here.

```toml tab="pyproject.toml"
[project]
...
dynamic = [
  "...",
]
```

## Metadata options

### Allowing direct references

By default, [dependencies](#dependencies) are not allowed to define [direct references](https://peps.python.org/pep-0440/#direct-references). To disable this check, set `allow-direct-references` to `true`:

```toml config-example
[tool.hatch.metadata]
allow-direct-references = true
```

### Allowing ambiguous features

By default, names of [optional dependencies](#optional) are normalized to prevent ambiguity. To disable this normalization, set `allow-ambiguous-features` to `true`:

```toml config-example
[tool.hatch.metadata]
allow-ambiguous-features = true
```

!!! danger "Deprecated"
    This option temporarily exists to provide better interoperability with tools that do not yet support [PEP 685](https://peps.python.org/pep-0685/) and will be removed in the first minor release after Jan 1, 2024.
