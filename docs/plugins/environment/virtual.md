# Virtual environment plugins

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
| `python` | | The version of Python to find on your system and subsequently use to create the environment, defaulting to the `HATCH_PYTHON` environment variable, followed by the first Python executable found along your PATH, followed by the Python executable Hatch is running on. For more information, see the [documentation](https://virtualenv.pypa.io/en/latest/user_guide.html#python-discovery). |
| `env:HATCH_ENV_TYPE_VIRTUAL_PATH` | | An explicit path to the virtual environment |
