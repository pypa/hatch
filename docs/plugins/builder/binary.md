# Binary builder

-----

This uses [PyApp](https://github.com/ofek/pyapp) to build an application that is able to bootstrap itself at runtime.

!!! note
    This requires an installation of [Rust](https://www.rust-lang.org). After installing, make sure the `CARGO` environment variable is set.

## Configuration

The builder plugin name is `binary`.

```toml config-example
[tool.hatch.build.targets.binary]
```

## Options

| Option           | Default                                | Description                                                                                                      |
|------------------|----------------------------------------|------------------------------------------------------------------------------------------------------------------|
| `scripts`        | all defined (if empty list)            | An array of defined [script](../../config/metadata.md#cli) names to limit what gets built                        |
| `python-version` | latest compatible Python minor version | The [Python version ID](https://ofek.dev/pyapp/latest/config/#known) to use                                      |
| `pyapp-version`  |                                        | The version of PyApp to use                                                                                      |
| `env-vars`       |                                        | Environment variables to set during the build process. See [below](#build-customization).                        |
| `outputs`        |                                        | An array of tables that each define options for an executable to be built. See [below](#build-customization).    |


## Build behavior

If any [scripts](../../config/metadata.md#cli) are defined then each one will be built (limited by the `scripts` option). Otherwise, a single executable will be built based on the project name assuming there is an equivalently named module with a `__main__.py` file.

Every executable will be built inside an `app` directory in the [output directory](../../config/build.md#output-directory).

If the `CARGO` environment variable is set then that path will be used as the executable for performing builds.

If the [`CARGO_BUILD_TARGET`](https://doc.rust-lang.org/cargo/reference/config.html#buildtarget) environment variable is set then its value will be appended to the file name stems.

If the `PYAPP_REPO` environment variable is set then a local build will be performed inside that directory rather than installing from [crates.io](https://crates.io). Note that this is [required](https://github.com/cross-rs/cross/issues/1215) if the `CARGO` environment variable refers to [cross](https://github.com/cross-rs/cross).


## Build customization

To customize how targets are built with the `binary` builder, you can define multiple outputs as an array of tables.

Each output is defined as a table with the following options:

| Option           | Default              | Description                                                                 |
|------------------|----------------------|-----------------------------------------------------------------------------|
| `exe-stem`       | `"{name}-{version}"` | The stem for the executable. `name` and `version` may be used as variables. |
| `env-vars`       |                      | Environment variables to set during the build process                       |

Additionally `env-vars` can also be defined at the top level to apply to all outputs.

The following example demonstrates how to build multiple executables with different settings:

```toml

[project]
name = "myapp"
version = "1.0.0"

[tool.hatch.build.targets.binary.env-vars]  # (2)!
CARGO_TARGET_DIR = "{root}/.tmp/pyapp_cargo"  # (1)!
PYAPP_DISTRIBUTION_EMBED = "false"
PYAPP_FULL_ISOLATION = "true"
PYAPP_PIP_EXTRA_ARGS = "--index-url ..."
PYAPP_UV_ENABLED = "true"
PYAPP_IS_GUI = "false"

[[tool.hatch.build.targets.binary.outputs]]  # (4)!
exe-stem = "{name}-cli"  # (5)!
env-vars = { "PYAPP_EXEC_SPEC" = "myapp.cli:cli" }  # (7)!

[[tool.hatch.build.targets.binary.outputs]]
exe-stem = "{name}-{version}"  # (6)!
env-vars = { "PYAPP_EXEC_SPEC" = "myapp.app:app", "PYAPP_IS_GUI" = "true" }  # (3)!
```

1. Context formating is supported in all `env-vars` values.
   In this case, the `CARGO_TARGET_DIR` environment variable is set to a local directory to speed up builds by caching.
2. The `env-vars` table at the top level is applied to all outputs. 
3. The `env-vars` table in an output is applied only to that output and has precedence over the top-level `env-vars`.
   In this case, we want the second outputs to be built as a GUI application.
4. The `outputs` table is an array of tables, each defining an output.
5. The `exe-stem` option is a format string that can use `name` and `version` as variables. On Windows
   the executable would be named for example `myapp-cli.exe`
6. The second output will be named `myapp-1.0.0.exe` on Windows.
7. The `PYAPP_EXEC_SPEC` environment variable is used to specify the entry point for the executable. 
   In this case, the `cli` function in the `myapp.cli` module is used for the first output.
   More info [here](https://ofek.dev/pyapp/latest/config/project/).

!!! note
    If no `outputs` array is defined but the `scripts` option is set, then the `outputs` table will be automatically 
    generated with the `exe-stem` set to `"<scriptname>-{version}"`. 

    You cannot define `outputs` and `scripts` at the same time.