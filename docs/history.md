# History

-----

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## **Hatch**

### Unreleased

***Added:***

- Support the absence of `pyproject.toml` files, as is the case for apps and non-Python projects
- Hide scripts that start with an underscore for the `env show` command by default
- Bump the minimum supported version of Hatchling to 1.4.0

***Fixed:***

- Keep environments in sync with the dependencies of the selected features
- Use `utf-8` for all files generated for new projects
- Normalize the package name to lowercase in `setuptools` migration script

### [1.2.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.2.1) - 2022-05-30 ### {: #hatch-v1.2.1 }

***Fixed:***

- Fix handling of top level `data_files` in `setuptools` migration script

### [1.2.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.2.0) - 2022-05-22 ### {: #hatch-v1.2.0 }

***Changed:***

- The `enter_shell` environment plugin method now accepts an additional `args` parameter

***Added:***

- Allow context string formatting for environment dependencies
- Add environment context string formatting fields `env_name`, `env_type`, `matrix`, `verbosity`, and `args`
- Support overriding the default arguments used to spawn shells on non-Windows systems
- Bump the minimum supported version of Hatchling to 1.3.0

***Fixed:***

- Improve `setuptools` migration script

### [1.1.2](https://github.com/pypa/hatch/releases/tag/hatch-v1.1.2) - 2022-05-20 ### {: #hatch-v1.1.2 }

***Fixed:***

- Bump the minimum supported version of Hatchling to 1.2.0
- Update project metadata to reflect support for Python 3.11

### [1.1.1](https://github.com/pypa/hatch/releases/tag/hatch-v1.1.1) - 2022-05-12 ### {: #hatch-v1.1.1 }

***Fixed:***

- Fix `setuptools` migration script for non-Windows systems

### [1.1.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.1.0) - 2022-05-12 ### {: #hatch-v1.1.0 }

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

### [1.0.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.0.0) - 2022-04-28 ### {: #hatch-v1.0.0 }

This is the first stable release of Hatch v1, a complete rewrite. Enjoy!

-----

## **Hatchling**

### Unreleased

### [1.4.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.4.0) - 2022-07-03 ### {: #hatchling-v1.4.0 }

***Changed:***

- The `packages` option uses the new `only-include` option to provide targeted inclusion, since that is desired most of the time. You can retain the old behavior by using the `include` and `sources` options together.

***Added:***

- Support PEP 561 type hinting
- Add `version` build hook
- Add `only-include` option
- The `editable` version of `wheel` targets now respects the `force-include` option by default
- The `force-include` option now supports path rewriting with the `sources` option
- The `wheel` target `shared-data` and `extra-metadata` options now respect file selection options
- The `wheel` target now auto-detects single module layouts
- Improve performance by never entering directories that are guaranteed to be undesirable like `__pycache__` rather than excluding individual files within
- Update SPDX license information to version 3.17

***Fixed:***

- Don't write empty entry points file for `wheel` targets if there are no entry points defined
- Allow metadata hooks to set the `version` in all cases
- Prevent duplicate file entries from inclusion when using the `force-include` option

### [1.3.1](https://github.com/pypa/hatch/releases/tag/hatchling-v1.3.1) - 2022-05-30 ### {: #hatchling-v1.3.1 }

***Fixed:***

- Better populate global variables for the `code` version source

### [1.3.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.3.0) - 2022-05-22 ### {: #hatchling-v1.3.0 }

***Removed:***

- Remove unused global `args` context string formatting field

***Added:***

- Improve error messages for the `env` context string formatting field

***Fixed:***

- Fix `uri` context string formatting modifier on Windows

### [1.2.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.2.0) - 2022-05-20 ### {: #hatchling-v1.2.0 }

***Added:***

- Allow context formatting for `project.dependencies` and `project.optional-dependencies`

### [1.1.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.1.0) - 2022-05-19 ### {: #hatchling-v1.1.0 }

***Added:***

- Add `uri` and `real` context string formatting modifiers for file system paths

### [1.0.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.0.0) - 2022-05-17 ### {: #hatchling-v1.0.0 }

***Changed:***

- Drop support for Python 2

***Added:***

- Improve error messaging for invalid versions
- Update project metadata to reflect support for Python 3.11

### [0.25.1](https://github.com/pypa/hatch/releases/tag/hatchling-v0.25.1) - 2022-06-14 ### {: #hatchling-v0.25.1 }

***Fixed:***

- Fix support for Windows on Python 2 by removing its support for symlinks

### [0.25.0](https://github.com/pypa/hatch/releases/tag/hatchling-v0.25.0) - 2022-05-15 ### {: #hatchling-v0.25.0 }

***Added:***

- Add `skip-excluded-dirs` build option
- Allow build data to add additional project dependencies for `wheel` and `sdist` build targets
- Add `force_include_editable` build data for the `wheel` build target
- Add `build_hooks` build data
- Add support for Mercurial's `.hgignore` files when using glob syntax
- Update project metadata to reflect the adoption by PyPA

***Fixed:***

- Properly use underscores for the name of `force_include` build data
- No longer greedily skip excluded directories by default

### [0.24.0](https://github.com/pypa/hatch/releases/tag/hatchling-v0.24.0) - 2022-04-28 ### {: #hatchling-v0.24.0 }

This is the initial public release of the Hatchling build system. Support for Python 2 will be dropped in version 1.
