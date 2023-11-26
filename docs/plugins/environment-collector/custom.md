# Custom environment collector

-----

This is a custom class in a given Python file that inherits from the [EnvironmentCollectorInterface](reference.md#hatch.env.collectors.plugin.interface.EnvironmentCollectorInterface).

## Configuration

The environment collector plugin name is `custom`.

```toml config-example
[tool.hatch.env.collectors.custom]
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `path` | `hatch_plugins.py` | The path of the Python file |

## Example

```python tab="hatch_plugins.py"
    from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface


    class CustomEnvironmentCollector(EnvironmentCollectorInterface):
        ...
```

If multiple subclasses are found, you must define a function named `get_environment_collector` that returns the desired environment collector.

!!! note
    Any defined [PLUGIN_NAME](reference.md#hatch.env.collectors.plugin.interface.EnvironmentCollectorInterface.PLUGIN_NAME) is ignored and will always be `custom`.
