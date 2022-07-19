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
