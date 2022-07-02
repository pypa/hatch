# Plugin utilities

-----

::: hatchling.builders.utils.get_reproducible_timestamp
    options:
      show_root_full_path: true

::: hatchling.builders.config.BuilderConfig
    options:
      show_source: false
      members:
      - directory
      - ignore_vcs
      - reproducible
      - dev_mode_dirs
      - versions
      - dependencies
      - default_include
      - default_exclude
      - default_packages

::: hatchling.bridge.app.Application
    options:
      show_source: false
      members:
      - abort
      - display_debug
      - display_error
      - display_info
      - display_success
      - display_waiting
      - display_warning

::: hatch.utils.platform.Platform
    options:
      show_source: false
      members:
      - format_for_subprocess
      - run_command
      - check_command
      - check_command_output
      - capture_process
      - exit_with_command
      - default_shell
      - modules
      - name
      - windows
      - macos
      - linux

::: hatch.env.context.EnvironmentContextFormatter
    options:
      show_source: false
      members:
      - formatters
