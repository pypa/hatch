# Hatch history

-----

All notable changes to Hatch will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## [1.15.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.15.1) - 2025-10-16 ## {: #hatch-v1.15.1 }

***Fixed:***

- Fix compatibility with cached default CPython distributions that were sourced from GitHub releases of the old owner

## [1.15.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.15.0) - 2025-10-15 ## {: #hatch-v1.15.0 }

***Changed:***

- Drop support for Python 3.8

***Added:***

- Support Python 3.14
- Upgrade default CPython distributions to 20251014
- Upgrade default PyPy distributions to 7.3.20

## [1.14.2](https://github.com/pypa/hatch/releases/tag/hatch-v1.14.2) - 2025-09-24 ## {: #hatch-v1.14.2 }

***Fixed:***

- Fix compatibility with recent versions of Click

## [1.14.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.14.1) - 2025-04-07 ## {: #hatch-v1.14.1 }

***Fixed:***

- Remove uses of the deprecated `--no-python-version-warning` flag when using pip

## [1.14.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.14.0) - 2024-12-16 ## {: #hatch-v1.14.0 }

***Added:***

- Upgrade default CPython distributions to 20241206
- Bump the minimum supported version of Hatchling to 1.26.3
- Update `virtualenv` dependency

## [1.13.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.13.0) - 2024-10-13 ## {: #hatch-v1.13.0 }

***Added:***

- Support managing Python 3.13 distributions

## [1.12.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.12.0) - 2024-05-28 ## {: #hatch-v1.12.0 }

***Changed:***

- The `run`/`env run` and `test` commands now treat inclusion variable options as an intersection rather than a union to allow for specific targeting of environments

***Added:***

- Add ability to control the source of Python distributions
- Upgrade Ruff to 0.4.5
- Upgrade PyApp to 0.22.0 for binary builds

***Fixed:***

- The `fmt` command no longer hides the commands that are being executed
- Add default timeout for network requests, useful when installing Python distributions
- Fix syntax highlighting contrast for the `config show` command

## [1.11.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.11.1) - 2024-05-23 ## {: #hatch-v1.11.1 }

***Added:***

- Add official GitHub Action for installing Hatch

***Fixed:***

- Fix `terminal.styles.spinner` configuration
- Fix entry points in the pre-built distributions that binaries use

## [1.11.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.11.0) - 2024-05-14 ## {: #hatch-v1.11.0 }

***Added:***

- Upgrade PyApp to 0.21.1 for binary builds

***Fixed:***

- On Linux, install the highest compatible Python distribution variant based on CPU architecture rather than assuming recent hardware

## [1.10.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.10.0) - 2024-05-02 ## {: #hatch-v1.10.0 }

***Changed:***

- The `run`/`env run`, `fmt` and `shell` commands now only change the current working directory to the project root if not already inside the project
- The `shell` command now accepts a single argument to specify the environment to enter which overrides the standard choice mechanisms. The arguments determining shell options have been converted to flags.

***Added:***

- Add `test` command
- The `run` command can now execute scripts that define inline metadata for dependencies and Python version constraints
- The `virtual` environment type now supports the ability to use UV in place of pip & virtualenv
- Add `self report` command for submitting pre-populated bug reports to GitHub
- The reserved environment used for static analysis is now completely configurable
- Add the following methods to the `environment` interface for complete control over output during life cycle management: `app_status_creation`, `app_status_pre_installation`, `app_status_post_installation`, `app_status_project_installation`, `app_status_dependency_state_check`, `app_status_dependency_installation_check`, `app_status_dependency_synchronization`
- Add binaries for 32-bit versions of Windows
- Read configuration from any `~/.pypirc` file for the `index` publisher
- Use the Git user as the default username for new project URL metadata
- Add `HATCH_DEBUG` environment variable that when enabled will show local variables in the case of unhandled tracebacks
- The `env show` command now outputs data about all internal environments when using the `--json` flag
- Upgrade default CPython distributions to 20240415
- Upgrade default PyPy distributions to 7.3.15
- Upgrade Ruff to 0.4.2
- Upgrade PyApp to 0.19.0 for binary builds
- Bump the minimum supported version of Hatchling to 1.24.2
- Bump the minimum supported version of virtualenv to 20.26.1

***Fixed:***

- Maintain consistent data paths for case insensitive file systems
- When projects derive dependencies from metadata hooks, there is now by default a status indicator for when the hooks are executed for better responsiveness
- Properly support projects with a `pyproject.toml` file but no `project` table e.g. applications
- Fix the `fmt` command when automatically installing plugin dependencies
- Fix dependency inheritance for the template of the `types` environment for new projects
- Fix warnings related to tar file extraction on Python 3.12+ when unpacking Python distributions for installation
- De-select Ruff rule `E501` for the `fmt` command by default since it conflicts with the formatter
- Fix colored output from build targets on the first run (build environment creation status indicator issue)
- Set the `packaging` dependency version as `>=23.2` to avoid its URL validation which can conflict with context formatting
- Fix the exit code when there happens to be an unhandled exception
- No longer capture both stdout and stderr streams when parsing metadata payloads from build environments
- Fix the `README.md` file template for new projects to avoid Markdown linting issues

## [1.9.7](https://github.com/pypa/hatch/releases/tag/hatch-v1.9.7) - 2024-04-24 ## {: #hatch-v1.9.7 }

***Fixed:***

- Limit the maximum version of virtualenv due to a backward incompatible change
- Upgrade PyApp to 0.12.0 for binary builds

## [1.9.4](https://github.com/pypa/hatch/releases/tag/hatch-v1.9.4) - 2024-03-12 ## {: #hatch-v1.9.4 }

***Fixed:***

- Limit the maximum version of Hatchling in anticipation of backward incompatible changes

## [1.9.3](https://github.com/pypa/hatch/releases/tag/hatch-v1.9.3) - 2024-01-25 ## {: #hatch-v1.9.3 }

***Fixed:***

- Fix loading of local plugins to account for newly released versions of a dependency

## [1.9.2](https://github.com/pypa/hatch/releases/tag/hatch-v1.9.2) - 2024-01-21 ## {: #hatch-v1.9.2 }

***Fixed:***

- Fix the default token variable name for publishing to PyPI

## [1.9.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.9.1) - 2023-12-25 ## {: #hatch-v1.9.1 }

***Fixed:***

- Ensure that the `dependency_hash` method of the `environment` interface is called after `sync_dependencies` for cases where the hash is only known at that point, such as for dependency lockers
- Only acknowledge the `HATCH_PYTHON_VARIANT_*` environment variables for Python resolution for supported platforms and architectures
- Fix Python resolution when there are metadata hooks with unsatisfied dependencies

## [1.9.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.9.0) - 2023-12-19 ## {: #hatch-v1.9.0 }

***Changed:***

- Environments prefixed by `hatch-` are now considered internal and used for special purposes such as configuration for static analysis

***Added:***

- Enable docstring formatting by default for static analysis
- Allow for overriding config of internal environments
- Concretely state the expected API contract for the environment interface methods `find` and `check_compatibility`
- Upgrade Ruff to 0.1.8
- Bump the minimum supported version of Hatchling to 1.21.0

***Fixed:***

- Ignore a project's Python requirement for environments where the project is not installed
- When not persisting config for static analysis, properly manage internal settings when Ruff's top level table already exists
- Ignore compatibility checks when environments have already been created, significantly improving performance of environment usage
- Properly allow overriding of the `path` option for the `virtual` environment type
- Fix nushell activation on non-Windows systems

## [1.8.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.8.1) - 2023-12-14 ## {: #hatch-v1.8.1 }

***Fixed:***

- Fix regression in calling subprocesses with updated PATH
- Fix automatic installation of environment plugins when running as a standalone binary
- Change default location of Python installations

## [1.8.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.8.0) - 2023-12-11 ## {: #hatch-v1.8.0 }

***Changed:***

- Drop support for Python 3.7
- The `get_build_process` method of the `environment` interface has been removed; plugins should use the new `run_builder` method instead
- Remove `pyperclip` dependency and the `--copy` flag of the `config find` command
- When running the `build` command all output from builders is now displayed as-is in real time without the stripping of ANSI codes
- Version information (for Hatch itself) is now derived from Git

***Added:***

- Support Python 3.12
- Add installers and standalone binaries
- Add the ability to manage Python installations
- Add `fmt` command
- The `virtual` environment type can now automatically download requested versions of Python that are not installed
- Add `dependency_hash` method to the `environment` interface
- The state of installed dependencies for environments is saved as metadata so if dependency definitions have not changed then no checking is performed, which can be computationally expensive
- The `build` command now supports backends other than Hatchling
- Allow the use of `features` for environments when `skip-install` is enabled
- The default is now `__token__` when prompting for a username for the `publish` command
- Add a new `run_builder` method to the `environment` interface
- Bump the minimum supported version of Hatchling to 1.19.0
- Bump the minimum supported version of `click` to 8.0.6

***Fixed:***

- Fix nushell activation
- Better handling of flat storage directory hierarchies for the `virtual` environment type
- Display useful information when running the `version` command outside of a project rather than erroring
- Fix the `project metadata` command by only capturing stdout from the backend
- Properly support Google Artifact Registry
- Fix parsing dependencies for environments when warnings are emitted

## [1.7.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.7.0) - 2023-04-03 ## {: #hatch-v1.7.0 }

***Changed:***

- The `src-layout` project template option is now enabled by default
- Non-critical output now goes to stderr

***Added:***

- Add `tool.hatch.env.requires` configuration to automatically install dependencies for environment and environment collector plugins
- Add `custom` environment collector
- Improve syncing of dependencies provided through Git direct references
- Add `isolated_data_directory` attribute to the environment interface
- Increase the timeout for and add retries to the `index` publisher
- Expand home and environment variables in configured cache and data directories
- Improve readability of exceptions
- Update project templates
- Bump the minimum supported version of Hatchling to 1.14.0

***Fixed:***

- Fix displaying the version with the `version` command when the version is static and build dependencies are unmet
- Fix build environments for the `virtual` environment type when storing within a relative path
- Work around System Integrity Protection on macOS when running commands
- Allow setuptools metadata migration for projects without `setup.py` if `setup.cfg` is present
- Handle additional edge cases for setuptools metadata migration
- Support boolean values for the `config set` command

## [1.6.3](https://github.com/pypa/hatch/releases/tag/hatch-v1.6.3) - 2022-10-24 ## {: #hatch-v1.6.3 }

***Fixed:***

- Fix `version` command when the version is dynamic and build dependencies are unmet

## [1.6.2](https://github.com/pypa/hatch/releases/tag/hatch-v1.6.2) - 2022-10-20 ## {: #hatch-v1.6.2 }

***Fixed:***

- Fix getting dynamic metadata from hooks for environments when dependencies are not dynamic

## [1.6.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.6.1) - 2022-10-16 ## {: #hatch-v1.6.1 }

***Fixed:***

- Computing the path to the user's home directory now gracefully falls back to `~` when it cannot be determined

## [1.6.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.6.0) - 2022-10-08 ## {: #hatch-v1.6.0 }

***Changed:***

- The `run_shell_command` environment interface method now accepts arbitrary `subprocess.Popen` keyword arguments. This is not strictly breaking, but will be utilized in upcoming features.
- The internal directory structure for storing `virtual` environments is now more nested. This is not breaking, but any local environments will be created anew.

***Added:***

- Add `project` command group to view details about the project like PEP 621 metadata
- Better support for auto-detection of environments by tools like Visual Studio Code now that the storage directory of `virtual` environments will be flat if Hatch's configured `virtual` environment directory resides somewhere within the project root or if it is set to a `.virtualenvs` directory within the user's home directory
- Build environments for the `virtual` environment type are now cached for improved performance
- Add `build_environment_exists` method to the environment interface for implementations that cache the build environment
- Add `path` option to the `virtual` environment type
- Add `--initialize-auth` flag to the `index` publisher to allow for the saving of authentication information before publishing
- Support Bash on Windows for the `shell` command
- The `setuptools` migration script no longer modifies the formatting of existing `pyproject.toml` configuration
- Bump the minimum supported version of Hatchling to 1.11.0

***Fixed:***

- Environments now respect dynamically defined project dependencies
- The `dep hash` and all `dep show` commands now respect dynamically defined project dependencies
- The `env show`, `dep hash`, and all `dep show` commands now honor context formatting
- Fix matrix variable inclusion filtering of the `run` and `env run` commands when there are multiple possible variables
- Build environment compatibility is now checked before use
- Decreasing verbosity now has no affect on output that should always be displayed
- Handle more edge cases in the `setuptools` migration script
- Environments now respect user defined environment variables for context formatting
- Update the scripts in the generated test environment template for new projects to reflect the documentation
- Allow `extra-dependencies` in environment overrides
- Depend on `packaging` explicitly rather than relying on it being a transitive dependency of Hatchling

## [1.5.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.5.0) - 2022-08-28 ## {: #hatch-v1.5.0 }

***Added:***

- The `index` publisher now recognizes repository-specific options
- Add the `--ignore-compat` flag to the `env run` command
- Setting the `HATCH_PYTHON` environment variable to `self` will now force the use of the Python executable Hatch is running on for `virtual` environment creation

***Fixed:***

- Fix the `--force-continue` flag of the `env run` command
- Handle more edge cases in the `setuptools` migration script

## [1.4.2](https://github.com/pypa/hatch/releases/tag/hatch-v1.4.2) - 2022-08-16 ## {: #hatch-v1.4.2 }

***Fixed:***

- Fix check for updating static versions with the `version` command when metadata hooks are in use

## [1.4.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.4.1) - 2022-08-13 ## {: #hatch-v1.4.1 }

***Fixed:***

- Fix non-detached inheritance disabling for environments

## [1.4.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.4.0) - 2022-08-06 ## {: #hatch-v1.4.0 }

***Added:***

- The default Python for `virtual` environments now checks PATH before using the one Hatch is running on
- Values for environment `env-vars` now support context formatting
- Add `name` override for environments to allow for regular expression matching
- The `index` publisher now better supports non-PyPI indices
- Add certificate options to the `index` publisher
- Display waiting text when checking dependencies and removing environments
- Display help text the first time the `shell` command is executed
- Update project templates with Python 3.11 and the latest versions of various GitHub Actions
- Add support for Almquist (`ash`) shells
- Add `hyperlink` as a dependency for better handling of package index URLs
- Bump the minimum supported version of `virtualenv` to 20.16.2
- Bump the minimum supported version of `tomlkit` to 0.11.1

***Fixed:***

- Acknowledge `extra-dependencies` for the `env show` command
- Fix locating executables within virtual environments on Debian
- Fix managing the terminal size inside the `shell` command
- Fix default code coverage file omission for the `src-layout` project template option

## [1.3.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.3.1) - 2022-07-11 ## {: #hatch-v1.3.1 }

***Fixed:***

- Support `-h`/`--help` flag for the `run` command

## [1.3.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.3.0) - 2022-07-10 ## {: #hatch-v1.3.0 }

***Changed:***

- Rename the default publishing plugin from `pypi` to the more generic `index`

***Added:***

- Support the absence of `pyproject.toml` files, as is the case for apps and non-Python projects
- Hide scripts that start with an underscore for the `env show` command by default
- Ignoring the exit codes of commands by prefixing with hyphens now works with entire named scripts
- Add a way to require confirmation for publishing
- Add `--force-continue` flag to the `env run` command
- Make tracebacks colorful and less verbose
- When shell configuration has not been defined, attempt to use the current shell based on parent processes before resorting to the defaults
- The shell name `pwsh` is now an alias for `powershell`
- Remove `atomicwrites` dependency
- Relax constraint on `userpath` dependency
- Bump the minimum supported version of Hatchling to 1.4.1

***Fixed:***

- Keep environments in sync with the dependencies of the selected features
- Use `utf-8` for all files generated for new projects
- Escape special characters Git may return in the user name when writing generated files for new projects
- Normalize the package name to lowercase in `setuptools` migration script
- Fix parsing of source distributions during publishing

## [1.2.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.2.1) - 2022-05-30 ## {: #hatch-v1.2.1 }

***Fixed:***

- Fix handling of top level `data_files` in `setuptools` migration script

## [1.2.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.2.0) - 2022-05-22 ## {: #hatch-v1.2.0 }

***Changed:***

- The `enter_shell` environment plugin method now accepts an additional `args` parameter

***Added:***

- Allow context string formatting for environment dependencies
- Add environment context string formatting fields `env_name`, `env_type`, `matrix`, `verbosity`, and `args`
- Support overriding the default arguments used to spawn shells on non-Windows systems
- Bump the minimum supported version of Hatchling to 1.3.0

***Fixed:***

- Improve `setuptools` migration script

## [1.1.2](https://github.com/pypa/hatch/releases/tag/hatch-v1.1.2) - 2022-05-20 ## {: #hatch-v1.1.2 }

***Fixed:***

- Bump the minimum supported version of Hatchling to 1.2.0
- Update project metadata to reflect support for Python 3.11

## [1.1.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.1.1) - 2022-05-12 ## {: #hatch-v1.1.1 }

***Fixed:***

- Fix `setuptools` migration script for non-Windows systems

## [1.1.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.1.0) - 2022-05-12 ## {: #hatch-v1.1.0 }

***Changed:***

- In order to simplify the implementation of command execution for environment plugins, the `run_shell_commands` method has been replaced by the singular `run_shell_command`. A new `command_context` method has been added to more easily satisfy complex use cases.
- The `finalize_command` environment plugin method has been removed in favor of the newly introduced context formatting functionality.

***Added:***

- Add context formatting functionality i.e. the ability to insert values into configuration like environment variables and command line arguments
- Any verbosity for command execution will now always display headers, even for single environments
- Every executed command is now displayed when running multiple commands or when verbosity is enabled
- Similar to `make`, ignore the exit code of executed commands that start with `-` (a hyphen)
- Add ability for the `--init` flag of the `new` command to automatically migrate `setuptools` configuration
- Update project metadata to reflect the adoption by PyPA and production stability

## [1.0.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.0.0) - 2022-04-28 ## {: #hatch-v1.0.0 }

This is the first stable release of Hatch v1, a complete rewrite. Enjoy!
