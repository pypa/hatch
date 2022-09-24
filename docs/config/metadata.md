# Project metadata

-----

Project metadata is stored in a `pyproject.toml` file located at the root of a project's tree
and is based entirely on [PEP 621][].

## Name (*required*) ## {: #name }

The name of the project.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
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

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
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

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
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

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
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

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project]
    ...
    keywords = [
      "...",
    ]
    ```

## Classifiers

The [trove classifiers](https://pypi.org/classifiers/) that apply to the project.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project]
    ...
    classifiers = [
      "...",
    ]
    ```

## URLs

A table of URLs where the key is the URL label and the value is the URL itself.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project.urls]
    Documentation = "..."
    "Source code" = "..."
    ```

## Dependencies

The format is based on [PEP 631][]. See the [dependency specification](dependency.md) section for more information.

Entries support [context formatting](context.md) and [disallow direct references](#allowing-direct-references) by default.

### Required

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project]
    ...
    dependencies = [
      "...",
    ]
    ```

### Optional

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
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

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
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

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project.gui-scripts]
    gui-name = "pkg.subpkg:func"
    ```

### Plugins

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project.entry-points.plugin-namespace]
    plugin-name1 = "pkg.subpkg1"
    plugin-name2 = "pkg.subpkg2:func"
    ```

## Dynamic

If any metadata fields are set dynamically, like the [`version`](#version) may be, then they must be listed here.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project]
    ...
    dynamic = [
      "...",
    ]
    ```

## Metadata options

### Allowing direct references

By default, [dependencies](#dependencies) are not allowed to define [direct references](https://peps.python.org/pep-0440/#direct-references). To disable this check, set `allow-direct-references` to `true`:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.metadata]
    allow-direct-references = true
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [metadata]
    allow-direct-references = true
    ```

### Allowing ambiguous features

By default, names of [optional dependencies](#optional) are normalized to prevent ambiguity. To disable this normalization, set `allow-ambiguous-features` to `true`:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.metadata]
    allow-ambiguous-features = true
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [metadata]
    allow-ambiguous-features = true
    ```

!!! danger "Deprecated"
    This option temporarily exists to provide better interoperability with tools that do not yet support [PEP 685](https://peps.python.org/pep-0685/) and will be removed in the first minor release after Jan 1, 2024.
