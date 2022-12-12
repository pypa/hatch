# Environment collector plugins

-----

Environment collectors allow for dynamically modifying environments or adding environments beyond those defined in config. Users can override default values provided by each environment.

## Installation

Any required environment collectors that are not built-in must be manually installed alongside Hatch or listed in the `tool.hatch.env.requires` array for automatic management:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.env]
    requires = [
      "...",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [env]
    requires = [
      "...",
    ]
    ```

::: hatch.env.collectors.plugin.interface.EnvironmentCollectorInterface
    options:
      members:
      - PLUGIN_NAME
      - root
      - config
      - get_initial_config
      - finalize_config
      - finalize_environments
