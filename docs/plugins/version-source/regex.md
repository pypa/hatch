# Regex version source

-----

See the documentation for [versioning](../../version.md).

## Updates

Setting the version is supported.

## Configuration

The version source plugin name is `regex`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.version]
    source = "regex"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [version]
    source = "regex"
    ```

## Options

| Option | Description |
| --- | --- |
| `path` (required) | A relative path to a file containing the project's version |
| `pattern` | A regular expression that has a named group called `version` that represents the version. The default pattern looks for a variable named `__version__` or `VERSION` that is set to a string containing the version, optionally prefixed with the lowercase letter `v`. |
