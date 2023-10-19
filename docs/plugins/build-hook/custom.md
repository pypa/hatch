# Custom build hook

-----

This is a custom class in a given Python file that inherits from the [BuildHookInterface](reference.md#hatchling.builders.hooks.plugin.interface.BuildHookInterface).

## Configuration

The build hook plugin name is `custom`.

```toml config-example
[tool.hatch.build.hooks.custom]
[tool.hatch.build.targets.<TARGET_NAME>.hooks.custom]
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `path` | `hatch_build.py` | The path of the Python file |

## Example

```python tab="hatch_build.py"
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    ...
```

If multiple subclasses are found, you must define a function named `get_build_hook` that returns the desired build hook.

!!! note
    Any defined [PLUGIN_NAME](reference.md#hatchling.builders.hooks.plugin.interface.BuildHookInterface.PLUGIN_NAME) is ignored and will always be `custom`.
