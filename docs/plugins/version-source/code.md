# Code version source

-----

## Updates

Setting the version is not supported.

## Configuration

The version source plugin name is `code`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.version]
    source = "code"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [version]
    source = "code"
    ```

## Options

| Option | Description |
| --- | --- |
| `path` (required) | A relative path to a Python file or extension module that will be loaded |
| `expression` | A Python expression that when evaluated in the context of the loaded file returns the version. The default expression is simply `__version__`. |
| `search-paths` | A list of relative paths to directories that will be prepended to Python's search path |

## Missing imports

If the chosen path imports another module in your project, then you'll need to use absolute imports coupled with the `search-paths` option. For example, say you need to load the following file:

=== ":octicons-file-code-16: src/pkg/\_\_init\_\_.py"

    ```python
    from ._version import get_version

    __version__ = get_version()
    ```

You should change it to:

=== ":octicons-file-code-16: src/pkg/\_\_init\_\_.py"

    ```python
    from pkg._version import get_version

    __version__ = get_version()
    ```

and the configuration would become:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.version]
    source = "code"
    path = "src/pkg/__init__.py"
    search-paths = ["src"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [version]
    source = "code"
    path = "src/pkg/__init__.py"
    search-paths = ["src"]
    ```
