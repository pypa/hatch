# Wheel builder

-----

A [wheel](https://packaging.python.org/specifications/binary-distribution-format/) is a binary distribution of a Python package that can be installed directly into an environment.

## Configuration

The builder plugin name is `wheel`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.wheel]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.wheel]
    ```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `core-metadata-version` | `"2.1"` | The version of [core metadata](https://packaging.python.org/specifications/core-metadata/) to use |
| `shared-data` | | A mapping similar to the [forced inclusion](../../config/build.md#forced-inclusion) option corresponding to [data](https://peps.python.org/pep-0427/#the-data-directory) that will be installed globally in a given Python environment, usually under `#!python sys.prefix` |
| `extra-metadata` | | A mapping similar to the [forced inclusion](../../config/build.md#forced-inclusion) option corresponding to extra [metadata](https://peps.python.org/pep-0427/#the-dist-info-directory) that will be shipped in a directory named `extra_metadata` |
| `strict-naming` | `true` | Whether or not file names should contain the normalized version of the project name |

## Versions

| Version | Description |
| --- | --- |
| `standard` (default) | The latest standardized format |
| `editable`           | A wheel that only ships `.pth` files or import hooks for real-time development |

## Default file selection

When the user has not set any [file selection](../../config/build.md#file-selection) options, the [project name](../../config/metadata.md#name) will be used to determine the package to ship in the following heuristic order:

1. `<NAME>/__init__.py`
2. `src/<NAME>/__init__.py`
3. `<NAME>.py`
4. `<NAMESPACE>/<NAME>/__init__.py`
5. Otherwise, every Python package and file that does not start with the word `test` will be included

## Reproducibility

[Reproducible builds](../../config/build.md#reproducible-builds) are supported.

## Build data

This is data that can be modified by [build hooks](../build-hook/reference.md).

| Data | Default | Description |
| --- | --- | --- |
| `tag` | | The full [tag](https://peps.python.org/pep-0425/) part of the filename (e.g. `py3-none-any`), defaulting to a cross-platform wheel with the supported major versions of Python based on [project metadata](../../config/metadata.md#python-support) |
| `infer_tag` | `#!python False` | When `tag` is not set, this may be enabled to use the one most specific to the platform, Python interpreter, and ABI |
| `pure_python` | `#!python True` | Whether or not to write metadata indicating that the package does not contain any platform-specific files |
| `dependencies` | | Extra [project dependencies](../../config/metadata.md#required) |
| `force_include_editable` | | Similar to the [`force_include` option](../build-hook/reference.md#build-data) but specifically for the `editable` [version](#versions) and takes precedence |
