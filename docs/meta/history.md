# History

-----

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## **Hatch**

### Unreleased

### [1rc2](https://github.com/ofek/hatch/releases/tag/hatch-v1rc2) - 2021-12-29 ### {: #hatch-v1rc2 }

This is the first release candidate for Hatch v1, a complete rewrite.

## **Hatchling**

### Unreleased

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
