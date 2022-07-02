# Custom metadata hook

-----

This is a custom class in a given Python file that inherits from the [MetadataHookInterface](reference.md#hatchling.metadata.plugin.interface.MetadataHookInterface).

## Configuration

The metadata hook plugin name is `custom`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.metadata.hooks.custom]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [metadata.hooks.custom]
    ```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `path` | `hatch_build.py` | The path of the Python file |

## Example

=== ":octicons-file-code-16: hatch_build.py"

    ```python
    from hatchling.metadata.plugin.interface import MetadataHookInterface


    class CustomMetadataHook(MetadataHookInterface):
        ...
    ```

If multiple subclasses are found, you must define a function named `get_metadata_hook` that returns the desired build hook.

!!! note
    Any defined [PLUGIN_NAME](reference.md#hatchling.metadata.plugin.interface.MetadataHookInterface.PLUGIN_NAME) is ignored and will always be `custom`.
