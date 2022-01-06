# History

-----

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## **Hatch**

### Unreleased

### [1rc6](https://github.com/ofek/hatch/releases/tag/hatch-v1rc6) - 2022-01-06 ### {: #hatch-v1rc6 }

***Added:***

- Bump the minimum supported version of Hatchling

### [1rc5](https://github.com/ofek/hatch/releases/tag/hatch-v1rc5) - 2022-01-02 ### {: #hatch-v1rc5 }

***Fixed:***

- Reduce default verbosity of config file creation for new users

### [1rc4](https://github.com/ofek/hatch/releases/tag/hatch-v1rc4) - 2022-01-01 ### {: #hatch-v1rc4 }

***Added:***

- Bump the minimum supported version of Hatchling

***Fixed:***

- Ensure Python subprocesses use unbuffered output to display real live progress
- Ensure that build environments honor environment variable filters

### [1rc3](https://github.com/ofek/hatch/releases/tag/hatch-v1rc3) - 2021-12-30 ### {: #hatch-v1rc3 }

***Added:***

- Bump the minimum supported version of Hatchling

### [1rc2](https://github.com/ofek/hatch/releases/tag/hatch-v1rc2) - 2021-12-29 ### {: #hatch-v1rc2 }

This is the first release candidate for Hatch v1, a complete rewrite.

-----

## **Hatchling**

### Unreleased

### [0.6](https://github.com/ofek/hatch/releases/tag/hatchling-v0.6) - 2022-01-06 ### {: #hatchling-v0.6 }

***Added:***

- Add ability to conditionally execute build hooks

***Fixed:***

- Disregard hook dependencies when building without hooks

### [0.5](https://github.com/ofek/hatch/releases/tag/hatchling-v0.5) - 2022-01-01 ### {: #hatchling-v0.5 }

***Added:***

- Add option to clean build hook artifacts after each build

***Fixed:***

- Properly include artifacts like C extensions that are built outside of package directories (with the intention of being placed directly inside `site-packages`) for projects with a `src`-layout structure
- For wheels, the ordering of generated `.dist-info` files now matches the ordering of files included from the local file system

### [0.4](https://github.com/ofek/hatch/releases/tag/hatchling-v0.4) - 2021-12-30 ### {: #hatchling-v0.4 }

***Changed:***

- In order to simplify configuration, build file selection options (`include`, `exclude`, etc.) can no longer be defined as comma separated strings.

***Added:***

- Refactor builder config handling into its own class
- Allow build hooks to access builder configuration

### [0.3.1](https://github.com/ofek/hatch/releases/tag/hatchling-v0.3.1) - 2021-12-30 ### {: #hatchling-v0.3.1 }

***Fixed:***

- Ignore non-Python files for [editable](https://github.com/pfmoore/editables) wheels

### [0.3](https://github.com/ofek/hatch/releases/tag/hatchling-v0.3) - 2021-12-29 ### {: #hatchling-v0.3 }

This is the initial public release of the Hatchling build system. Support for Python 2 will be dropped in version 1.
