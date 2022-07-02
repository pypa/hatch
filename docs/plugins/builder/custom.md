# Custom builder

-----

This is a custom class in a given Python file that inherits from the [BuilderInterface](reference.md#hatchling.builders.plugin.interface.BuilderInterface).

## Configuration

The builder plugin name is `custom`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.custom]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.custom]
    ```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `path` | `hatch_build.py` | The path of the Python file |

## Example

=== ":octicons-file-code-16: hatch_build.py"

    ```python
    from hatchling.builders.plugin.interface import BuilderInterface


    class CustomBuilder(BuilderInterface):
        ...
    ```

If multiple subclasses are found, you must define a function named `get_builder` that returns the desired builder.

!!! note
    Any defined [PLUGIN_NAME](reference.md#hatchling.builders.plugin.interface.BuilderInterface.PLUGIN_NAME) is ignored and will always be `custom`.
