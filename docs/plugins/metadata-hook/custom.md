# Custom metadata hook

-----

This is a custom class in a given Python file that inherits from the [MetadataHookInterface](reference.md#hatchling.metadata.plugin.interface.MetadataHookInterface).

## Configuration

The metadata hook plugin name is `custom`.

```toml config-example
[tool.hatch.metadata.hooks.custom]
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `path` | `hatch_build.py` | The path of the Python file |

## Example

```python tab="hatch_build.py"
    from hatchling.metadata.plugin.interface import MetadataHookInterface


    class CustomMetadataHook(MetadataHookInterface):
        ...
```

If multiple subclasses are found, you must define a function named `get_metadata_hook` that returns the desired build hook.

!!! note
    Any defined [PLUGIN_NAME](reference.md#hatchling.metadata.plugin.interface.MetadataHookInterface.PLUGIN_NAME) is ignored and will always be `custom`.
