# Version scheme plugins

-----

## Built-in

### Standard

See the documentation for [versioning](../version.md#updating).

#### Configuration

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

::: hatch.version.scheme.plugin.interface.VersionSchemeInterface
    selection:
      members:
      - PLUGIN_NAME
      - root
      - config
      - update
