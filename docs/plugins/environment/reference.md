# Environment plugins

-----

See the documentation for [environment configuration](../../config/environment/overview.md).

## Known third-party

- [hatch-conda](https://github.com/OldGrumpyViking/hatch-conda) - environments backed by Conda/Mamba
- [hatch-containers](https://github.com/ofek/hatch-containers) - environments run inside containers
- [hatch-pip-compile](https://github.com/juftin/hatch-pip-compile) - use [pip-compile](https://github.com/jazzband/pip-tools) to manage project dependencies and lockfiles
- [hatch-pip-deepfreeze](https://github.com/sbidoul/hatch-pip-deepfreeze) - [virtual](virtual.md) environments with dependency locking by [pip-deepfreeze](https://github.com/sbidoul/pip-deepfreeze)

## Installation

Any required environment types that are not built-in must be manually installed alongside Hatch or listed in the `tool.hatch.env.requires` array for automatic management:

```toml config-example
[tool.hatch.env]
requires = [
  "...",
]
```

## Life cycle

Whenever an environment is used, the following logic is performed:

::: hatch.cli.application.Application.prepare_environment
    options:
      show_root_heading: false
      show_root_toc_entry: false

## Build environments

All environment types should [offer support](#hatch.env.plugin.interface.EnvironmentInterface.build_environment) for a special sub-environment in which projects can be built. This environment is used in the following scenarios:

- the [`build`](../../cli/reference.md#hatch-build) command
- commands that read dependencies, like [`dep hash`](../../cli/reference.md#hatch-dep-hash), if any [project dependencies](../../config/metadata.md#dependencies) are [set dynamically](../../config/metadata.md#dynamic)

::: hatch.env.plugin.interface.EnvironmentInterface
    options:
      members:
      - PLUGIN_NAME
      - app
      - root
      - name
      - data_directory
      - isolated_data_directory
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
      - dependency_hash
      - build_environment
      - build_environment_exists
      - run_builder
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
