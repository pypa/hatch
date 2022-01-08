# Plugin utilities

-----

::: hatchling.builders.utils.get_reproducible_timestamp
    rendering:
      show_root_full_path: true

::: hatchling.builders.config.BuilderConfig
    rendering:
      show_source: false
    selection:
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
    rendering:
      show_source: false
    selection:
      members:
      - abort
      - display_debug
      - display_error
      - display_info
      - display_success
      - display_waiting
      - display_warning

::: hatch.utils.platform.Platform
    rendering:
      show_source: false
    selection:
      members:
      - format_for_subprocess
      - run_command
      - check_command
      - check_command_output
      - capture_process
      - exit_with_command
      - default_shell
      - name
      - windows
      - macos
      - linux
