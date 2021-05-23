# Environment collector

-----

Environment collectors allow for adding environments beyond those defined in config. Users can override default values provided by each environment.

## Built-in

### Default

This adds the `default` environment with [type](../config/environment.md#type) set to [virtual](environment.md#virtual) and will always be applied.

#### Configuration

The environment plugin name is `default`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.env.collectors.default]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [env.collectors.default]
    ```

::: hatch.env.collectors.plugin.interface.EnvironmentCollectorInterface
    selection:
      members:
      - PLUGIN_NAME
      - root
      - config
      - get_environment_config
