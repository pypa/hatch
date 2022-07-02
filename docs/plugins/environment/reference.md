# Environment plugins

-----

See the documentation for [environment configuration](../../config/environment/overview.md).

## Known third-party

- [hatch-containers](https://github.com/ofek/hatch-containers) - environments run inside containers

## Life cycle

Whenever an environment is used, the following logic is performed:

::: hatch.cli.application.Application.prepare_environment
    options:
      show_root_heading: false
      show_root_toc_entry: false

::: hatch.env.plugin.interface.EnvironmentInterface
    options:
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
      - description
      - activate
      - deactivate
      - find
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
      - command_context
      - enter_shell
      - run_shell_command
      - resolve_commands
      - get_env_vars
      - apply_features
      - construct_pip_install_command
      - join_command_args
      - check_compatibility
      - get_option_types
      - get_env_var_option
      - get_context
