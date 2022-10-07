# Standard version scheme

-----

See the documentation for [versioning](../../version.md#updating).

## Configuration

The version scheme plugin name is `standard`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.version]
    scheme = "standard"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [version]
    scheme = "standard"
    ```

## Options

| Option | Description |
| --- | --- |
| `validate-bump` | When setting a specific version, this determines whether to check that the new version is higher than the original. The default is `true`. |
