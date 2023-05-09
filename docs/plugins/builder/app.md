# Application builder

-----

This uses [PyApp](https://github.com/ofek/pyapp) to build an application that is able to bootstrap itself at runtime.

!!! note
    This requires an installation of [Rust](https://www.rust-lang.org).

## Configuration

The builder plugin name is `app`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.app]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.app]
    ```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `scripts` | all defined | An array of defined [script](../../config/metadata.md#cli) names to limit what gets built |
| `python-version` | latest compatible Python minor version | The exact Python version to use |
| `pyapp-version` | | The version of PyApp to use |

## Build behavior

If any [scripts](../../config/metadata.md#cli) are defined then each one will be built (limited by the `scripts` option). Otherwise, a single executable will be built based on the project name assuming there is an equivalently named module with a `__main__.py` file.

Every executable will be built inside an `app` directory in the [output directory](../../config/build.md#output-directory).

If the [`CARGO_BUILD_TARGET`](https://doc.rust-lang.org/cargo/reference/config.html#buildtarget) environment variable is set then it's value will be appended to the file name stems.
