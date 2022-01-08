# Builder plugins

-----

See the documentation for [build configuration](../config/build.md).

## Built-in

### Wheel

A [wheel](https://packaging.python.org/specifications/binary-distribution-format/) is a binary distribution of a Python package that can be installed directly into an environment.

#### Configuration

The builder plugin name is `wheel`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.wheel]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.wheel]
    ```

##### Options

| Option | Default | Description |
| --- | --- | --- |
| `zip-safe` | `true` | Whether or not to write metadata indicating that the package is able to run directly as a ZIP file; can be [overriden by build hooks](#build-data) |
| `core-metadata-version` | `"2.3"` | The version of [core metadata](https://packaging.python.org/specifications/core-metadata/) to use |

!!! tip
    The `zip-safe` option must be set to `false` for packages that indicate [PEP 561](https://www.python.org/dev/peps/pep-0561/) typing support with a `py.typed` file.

##### Versions

| Version | Description |
| --- | --- |
| `standard` (default) | The latest standardized format |

#### Default file selection

When the user has not set any [file selection](../config/build.md#file-selection) options, the [project name](../config/metadata.md#name) will be used to determine the package to ship in the following heuristic order:

1. `<PACKAGE>/__init__.py`
2. `src/<PACKAGE>/__init__.py`
3. `<NAMESPACE>/<PACKAGE>/__init__.py`
4. Otherwise, every Python package and file that does not start with the word `test` will be included

#### Reproducibility

[Reproducible builds](../config/build.md#reproducible-builds) are supported.

#### Build data

This is data that can be modified by [build hooks](build-hook.md).

| Data | Default | Description |
| --- | --- | --- |
| `tag` | | The full [tag](https://www.python.org/dev/peps/pep-0425/) part of the filename (e.g. `py3-none-any`), defaulting to a cross-platform wheel with the supported major versions of Python based on [project metadata](../config/metadata.md#python-support) |
| `infer_tag` | `#!python False` | When `tag` is not set, this may be enabled to use the one most specific to the platform, Python interpreter, and ABI |
| `zip_safe` | | Whether or not to write metadata indicating that the package is able to run directly as a ZIP file, defaulting to the `zip-safe` [option](#options) |

### Source distribution

A source distribution, or `sdist`, is an archive of Python "source code". Although largely unspecified, by convention it should include everything that is required to build a [wheel](#wheel) without making network requests.

#### Configuration

The builder plugin name is `sdist`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.sdist]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.sdist]
    ```

##### Options

| Option | Default | Description |
| --- | --- | --- |
| `support-legacy` | `false` | Whether or not to include a `setup.py` file to support legacy installation mechanisms |
| `core-metadata-version` | `"1.2"` | The version of [core metadata](https://packaging.python.org/specifications/core-metadata/) to use |

##### Versions

| Version | Description |
| --- | --- |
| `standard` (default) | The latest conventional format |

#### Default file selection

When the user has not set any [file selection](../config/build.md#file-selection) options, all files that are not [ignored by your VCS](../config/build.md#vcs) will be included.

#### Reproducibility

[Reproducible builds](../config/build.md#reproducible-builds) are supported.

### Custom

This is a custom class in a given Python file that inherits from the [BuilderInterface](#hatchling.builders.plugin.interface.BuilderInterface).

#### Configuration

The builder plugin name is `custom`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.custom]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.custom]
    ```

An option `path` is used to specify the path of the Python file, defaulting to `build.py`.

#### Example

=== ":octicons-file-code-16: build.py"

    ```python
    from hatchling.builders.plugin.interface import BuilderInterface


    class CustomBuilder(BuilderInterface):
        ...
    ```

If multiple subclasses are found, you must define a function named `get_builder` that returns the desired builder.

!!! note
    Any defined [PLUGIN_NAME](#hatchling.builders.plugin.interface.BuilderInterface.PLUGIN_NAME) is ignored and will always be `custom`.

::: hatchling.builders.plugin.interface.BuilderInterface
    selection:
      members:
      - PLUGIN_NAME
      - app
      - root
      - build_config
      - target_config
      - config
      - get_config_class
      - get_version_api
      - get_default_versions
      - clean
      - recurse_project_files
      - get_default_build_data
