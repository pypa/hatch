# Environment version source

-----

Retrieves the version from an environment variable. This can be useful in build pipelines where the version is set by an external trigger.

## Updates

Setting the version is not supported.

## Configuration

The version source plugin name is `env`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.version]
    source = "env"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [version]
    source = "env"
    ```

## Options

| Option | Description |
| --- | --- |
| `variable` (required) | The name of the environment variable |
