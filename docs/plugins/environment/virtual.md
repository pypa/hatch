# Virtual environment

-----

This uses virtual environments backed by the standard [virtualenv](https://github.com/pypa/virtualenv) tool.

## Configuration

The environment plugin name is `virtual`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    type = "virtual"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [envs.<ENV_NAME>]
    type = "virtual"
    ```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `system-packages` | `false` | Whether or not to give the virtual environment access to the system `site-packages` directory |
| `python` | | The version of Python to find on your system and subsequently use to create the environment, defaulting to the `HATCH_PYTHON` environment variable, followed by the first Python executable found along your PATH, followed by the Python executable Hatch is running on. Setting the `HATCH_PYTHON` environment variable to `self` will force the use of the Python executable Hatch is running on. For more information, see the [documentation](https://virtualenv.pypa.io/en/latest/user_guide.html#python-discovery). |
| `path` | | An explicit path to the virtual environment. The path may be absolute or relative to the project root. Any environments that [inherit](../../config/environment/overview.md#inheritance) this option will also use this path. The environment variable `HATCH_ENV_TYPE_VIRTUAL_PATH` may be used, which will take precedence. |

## Location

The [location](../../cli/reference.md#hatch-env-find) of environments is determined in the following heuristic order:

1. The `path` option
2. A directory named after the environment within the configured `virtual` [environment directory](../../config/hatch.md#environments) if the directory resides somewhere within the project root or if it is set to a `.virtualenvs` directory within the user's home directory
3. Otherwise, environments are stored within the configured `virtual` [environment directory](../../config/hatch.md#environments) in a deeply nested structure in order to support multiple projects

Additionally, when the `path` option is not used, the name of the directory for the `default` environment will be the normalized project name to provide a more meaningful default [shell](../../cli/reference.md#hatch-shell) prompt.

## Troubleshooting

### macOS SIP

If you need to set linker environment variables like those starting with `DYLD_` or `LD_`, any executable secured by [System Integrity Protection](https://en.wikipedia.org/wiki/System_Integrity_Protection) that is invoked when [running commands](../../environment.md#command-execution) will not see those environment variable modifications as macOS strips those.

Hatch interprets such commands as shell commands but deliberately ignores such paths to protected shells. This workaround suffices for the majority of use cases but there are 2 situations in which it may not:

1. There are no unprotected `sh`, `bash`, `zsh`, nor `fish` executables found along PATH.
2. The desired executable is a project's [script](../../config/metadata.md#cli), and the [location](#location) of environments contains spaces or is longer than 124[^1] characters. In this case `pip` and other installers will create such an entry point with a shebang pointing to `/bin/sh` (which is protected) to avoid shebang limitations. Rather than changing the location, you could invoke the script as e.g. `python -m pytest` (if the project supports that method of invocation by shipping a `__main__.py`).

[^1]: The shebang length limit is [usually](https://web.archive.org/web/20221231220856/https://www.in-ulm.de/~mascheck/various/shebang/#length) 127 but 3 characters surround the executable path: `#!<EXE_PATH>\n`
