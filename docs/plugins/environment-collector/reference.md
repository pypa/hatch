# Environment collector plugins

-----

Environment collectors allow for dynamically modifying environments or adding environments beyond those defined in config. Users can override default values provided by each environment.

::: hatch.env.collectors.plugin.interface.EnvironmentCollectorInterface
    options:
      members:
      - PLUGIN_NAME
      - root
      - config
      - get_initial_config
      - finalize_config
      - finalize_environments
