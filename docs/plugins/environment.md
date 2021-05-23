# Environment plugins

-----

See the documentation for [environment configuration](../config/environment.md).

## Known third-party

- [hatch-containers](https://github.com/ofek/hatch-containers) - environments run inside containers

## Life cycle

Whenever an environment is used, the following logic is performed:

::: hatch.cli.application.Application.prepare_environment
    rendering:
      show_root_heading: false
      show_root_toc_entry: false

## Built-in

### Virtual

This uses virtual environments backed by the standard [virtualenv](https://github.com/pypa/virtualenv) tool.

#### Configuration

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

##### Options

| Option | Default | Description |
| --- | --- | --- |
| `system-packages` | `false` | Whether or not to give the virtual environment access to the system `site-packages` directory |
| `python` | | The version of Python to find on your system and subsequently use to create the environment, defaulting to the first `python` found along your `PATH`, followed by the Python executable Hatch is running on. For more information, see the [documentation](https://virtualenv.pypa.io/en/latest/user_guide.html#python-discovery). |

::: hatch.env.plugin.interface.EnvironmentInterface
    selection:
      members:
      - PLUGIN_NAME
      - app
      - root
      - name
      - data_directory
      - config
      - platform
      - environment_dependencies
      - dependencies
      - env_vars
      - env_include
      - env_exclude
      - platforms
      - skip_install
      - dev_mode
      - activate
      - deactivate
      - create
      - remove
      - exists
      - install_project
      - install_project_dev_mode
      - dependencies_in_sync
      - sync_dependencies
      - build_environment
      - get_build_process
      - construct_build_command
      - enter_shell
      - run_shell_commands
      - resolve_commands
      - finalize_command
      - get_env_vars
      - apply_features
      - construct_pip_install_command
      - join_command_args
      - check_compatibility
      - get_option_types
