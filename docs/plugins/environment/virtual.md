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
