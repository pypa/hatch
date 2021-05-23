# Metadata hook plugins

-----

Metadata hooks allow for the modification of [project metadata](../config/metadata.md) after it has been loaded.

## Built-in

### Custom

This is a custom class in a given Python file that inherits from the [MetadataHookInterface](#hatchling.metadata.plugin.interface.MetadataHookInterface).

#### Configuration

The metadata hook plugin name is `custom`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.metadata.custom]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [metadata.custom]
    ```

An option `path` is used to specify the path of the Python file, defaulting to `build.py`.

#### Example

=== ":octicons-file-code-16: build.py"

    ```python
    from hatchling.metadata.plugin.interface import MetadataHookInterface


    class CustomMetadataHook(MetadataHookInterface):
        ...
    ```

If multiple subclasses are found, you must define a function named `get_metadata_hook` that returns the desired build hook.

!!! note
    Any defined [PLUGIN_NAME](#hatchling.metadata.plugin.interface.MetadataHookInterface.PLUGIN_NAME) is ignored and will always be `custom`.

::: hatchling.metadata.plugin.interface.MetadataHookInterface
    selection:
      members:
      - PLUGIN_NAME
      - root
      - config
      - update
