# History

-----

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## **Hatch**

### Unreleased

***Changed:***

- In order to simplify the implementation of command execution for environment plugins, the `run_shell_commands` method has been replaced by the singular `run_shell_command`. A new `command_context` method has been added to more easily satisfy complex use cases.
- The `finalize_command` environment plugin method has been removed in favor of the newly introduced context formatting functionality.

***Added:***

- Add context formatting functionality i.e. the ability to insert values into configuration like environment variables and command line arguments
- Add `--show-headers` option to the `env run` command to always display headers, even for single environments
- Similar to `make`, ignore the exit code of executed commands that start with `-` (a hyphen)
- Update project metadata to reflect the adoption by PyPA

### [1.0.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.0.0) - 2022-04-28 ### {: #hatch-v1.0.0 }

This is the first stable release of Hatch v1, a complete rewrite. Enjoy!

-----

## **Hatchling**

### Unreleased

***Added:***

- Update project metadata to reflect the adoption by PyPA

### [0.24.0](https://github.com/pypa/hatch/releases/tag/hatchling-v0.24.0) - 2022-04-28 ### {: #hatchling-v0.24.0 }

This is the initial public release of the Hatchling build system. Support for Python 2 will be dropped in version 1.
