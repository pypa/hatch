# Environment version source

-----

Retrieves the version from an environment variable. This can be useful in build pipelines where the version is set by an external trigger.

## Updates

Setting the version is supported and modifies the environment variable. How long this actually persists depends on your operating environment. It is usually safer to just change the environment variable.

## Configuration

The version source plugin name is `env`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.version]
    source = "env"
    variable = "BUILD_TAG"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [version]
    source = "env"
    variable = "BUILD_TAG"
    ```

## Options

| Option | Description |
| --- | --- |
| `variable` (required) | The name of the environment variable. |
