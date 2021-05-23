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
        The file extension must be `.md` or `.rst`.

        ```toml
        [project]
        ...
        readme = "README.md"
        ```

    === "Complex"
        The `content_type` field must be set to `text/markdown` or `text/x-rst`.

        === "File"
            A `charset` field may also be set to instruct which encoding to
            use for reading the file, defaulting to `utf-8`.

            ```toml
            [project]
            ...
            readme = {"file": "README.md", "content_type": "text/markdown"}
            ```

        === "Text"
            The `content_type` field must be set to `text/markdown` or `text/x-rst`.

            ```toml
            [project]
            ...
            readme = {"text": "...", "content_type": "text/markdown"}
            ```

!!! note
    If this is defined as a file, then it will always be included in [source distributions](../plugins/builder.md#source-distribution) for consistent builds.

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

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [project.scripts]
    cli-name = "pkg.subpkg:func"
    ```

### GUI

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
