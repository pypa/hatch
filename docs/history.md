# History

-----

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## **Hatch**

### Unreleased

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
