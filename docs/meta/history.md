# History

-----

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## **Hatch**

### Unreleased

### [1.0.0rc15](https://github.com/ofek/hatch/releases/tag/hatch-v1.0.0rc15) - 2022-03-18 ### {: #hatch-v1.0.0rc15 }

***Added:***

- Bump the minimum supported version of Hatchling

### [1.0.0rc14](https://github.com/ofek/hatch/releases/tag/hatch-v1.0.0rc14) - 2022-03-06 ### {: #hatch-v1.0.0rc14 }

***Added:***

- When building with no targets defined in config, default to `-t sdist -t wheel` rather than raising an error
- Improve the output format of the `env show` command
- Add `description` option to environments
- Add `extra-dependencies` option to environments
- Upgrade `actions/setup-python` action of the CI option for new projects to `v3`
- Bump the minimum supported version of Hatchling
- Update project metadata

### [1.0.0rc13](https://github.com/ofek/hatch/releases/tag/hatch-v1.0.0rc13) - 2022-02-13 ### {: #hatch-v1.0.0rc13 }

***Added:***

- Update dependencies

***Fixed:***

- Remove the forced use of embedded seed packages for `virtual` environments since distributions like Debian and Fedora do not use those

### [1.0.0rc12](https://github.com/ofek/hatch/releases/tag/hatch-v1.0.0rc12) - 2022-02-05 ### {: #hatch-v1.0.0rc12 }

***Added:***

- Switch project to a `src`-layout structure
- Update dependencies

### [1.0.0rc11](https://github.com/ofek/hatch/releases/tag/hatch-v1.0.0rc11) - 2022-01-23 ### {: #hatch-v1.0.0rc11 }

***Changed:***

- Change environment storage configuration to allow for exact paths per type of environment
- Add new required method `find` to the environment interface

***Added:***

- Add more informative help text for the arguments of the `run` command

### [1.0.0rc10](https://github.com/ofek/hatch/releases/tag/hatch-v1.0.0rc10) - 2022-01-19 ### {: #hatch-v1.0.0rc10 }

***Fixed:***

- Handle edge case for displaying text while showing a status message

### [1.0.0rc9](https://github.com/ofek/hatch/releases/tag/hatch-v1.0.0rc9) - 2022-01-18 ### {: #hatch-v1.0.0rc9 }

***Added:***

- Add ability to set the non-preview variant of versions
- Improve collection of information about Python interpreters within environments
- Update dependencies

***Fixed:***

- Relax restriction on the contents of `build-system.requires`
- The `version` command now properly handles statically defined versions
- Fix typo preventing the Python executable fallback for environments when there is no `python` along `PATH`

### [1.0.0rc8](https://github.com/ofek/hatch/releases/tag/hatch-v1.0.0rc8) - 2022-01-08 ### {: #hatch-v1.0.0rc8 }

***Added:***

- Support Python 3.7

### [1.0.0rc7](https://github.com/ofek/hatch/releases/tag/hatch-v1.0.0rc7) - 2022-01-08 ### {: #hatch-v1.0.0rc7 }

***Added:***

- Bump the minimum supported version of Hatchling

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

### [0.21.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.21.0) - 2022-03-17 ### {: #hatchling-v0.21.0 }

***Changed:***

- In order to simplify configuration, metadata hooks are now configured under `tool.hatch.metadata.hooks` rather than directly under `tool.hatch.metadata`

***Added:***

- Add option to allow the use of direct references for dependencies
- Make the default pattern for the `regex` version source case insensitive
- Deduplicate and normalize dependency definitions before writing metadata for wheels and source distributions
- Normalize the names of optional dependency groups to adhere to the newly-introduced [PEP 685](https://www.python.org/dev/peps/pep-0685/)

### [0.20.1](https://github.com/ofek/hatch/releases/tag/hatchling-v0.20.1) - 2022-03-07 ### {: #hatchling-v0.20.1 }

***Fixed:***

- Allow test execution from within Hatchling's source distribution

### [0.20.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.20.0) - 2022-03-07 ### {: #hatchling-v0.20.0 }

***Added:***

- Relax dependency constraints

### [0.19.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.19.0) - 2022-03-06 ### {: #hatchling-v0.19.0 }

***Added:***

- Add option for builds to declare dependence on a project's runtime dependencies

***Fixed:***

- Disallow direct references for dependency definitions

### [0.18.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.18.0) - 2022-02-27 ### {: #hatchling-v0.18.0 }

***Added:***

- Add ability to rewrite the distributed path of files

### [0.17.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.17.0) - 2022-02-26 ### {: #hatchling-v0.17.0 }

***Added:***

- Always include any root `.gitignore` file for source distributions so recursive builds are guaranteed to be identical

***Fixed:***

- Fix metadata handling of non-ASCII characters in README files for source distributions on Python 2

### [0.16.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.16.0) - 2022-02-26 ### {: #hatchling-v0.16.0 }

***Added:***

- Always include the default build script location for source distributions
- Automatically remove fields from `project.dynamic` that were added by metadata hooks

### [0.15.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.15.0) - 2022-02-23 ### {: #hatchling-v0.15.0 }

***Added:***

- Fail builds early for invalid project metadata
- When building with no targets defined in config, default to `-t sdist -t wheel` rather than raising an error
- Update project metadata

### [0.14.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.14.0) - 2022-02-16 ### {: #hatchling-v0.14.0 }

***Added:***

- Add `code` version source that can load arbitrary Python code

***Fixed:***

- Also exclude compiled Python extensions by default for cases where there is no `.gitignore`

### [0.13.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.13.0) - 2022-02-16 ### {: #hatchling-v0.13.0 }

***Added:***

- Exclude Python byte code files by default for cases where there is no Git checkout and therefore no `.gitignore` file providing default exclusion patterns

***Fixed:***

- Fix metadata handling of non-ASCII characters in README files on Python 2

### [0.12.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.12.0) - 2022-02-13 ### {: #hatchling-v0.12.0 }

***Added:***

- Add option to exclude non-artifact files that do not reside within a Python package

### [0.11.3](https://github.com/ofek/hatch/releases/tag/hatchling-v0.11.3) - 2022-02-13 ### {: #hatchling-v0.11.3 }

***Fixed:***

- Replace the build data `zip_safe` with `pure_python`

### [0.11.2](https://github.com/ofek/hatch/releases/tag/hatchling-v0.11.2) - 2022-02-05 ### {: #hatchling-v0.11.2 }

***Fixed:***

- Fix custom hooks on Python 2

### [0.11.1](https://github.com/ofek/hatch/releases/tag/hatchling-v0.11.1) - 2022-02-05 ### {: #hatchling-v0.11.1 }

***Fixed:***

- Change the default location of custom build scripts from `build.py` to `hatch_build.py` so the packaging tool [build](https://github.com/pypa/build) can be used (if desired) at the project root

### [0.11.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.11.0) - 2022-02-04 ### {: #hatchling-v0.11.0 }

***Added:***

- Switch project to a `src`-layout structure
- Ship downstream tests with `hatchling` source distributions

***Fixed:***

- Ship license with `hatchling`

### [0.10.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.10.0) - 2022-01-20 ### {: #hatchling-v0.10.0 }

***Added:***

- Support `text/plain` content type for `project.readme` metadata

### [0.9.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.9.0) - 2022-01-18 ### {: #hatchling-v0.9.0 }

***Added:***

- Build hooks now have access to project metadata

***Fixed:***

- Improve check for satisfied dependencies

### [0.8.2](https://github.com/ofek/hatch/releases/tag/hatchling-v0.8.2) - 2022-01-16 ### {: #hatchling-v0.8.2 }

***Fixed:***

- Fix plugins on Python 2

### [0.8.1](https://github.com/ofek/hatch/releases/tag/hatchling-v0.8.1) - 2022-01-14 ### {: #hatchling-v0.8.1 }

***Fixed:***

- Update project metadata

### [0.8.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.8.0) - 2022-01-09 ### {: #hatchling-v0.8.0 }

***Added:***

- The `regex` version source now supports the `^`/`$` multi-line characters by default

***Fixed:***

- Fix greedy matching in the default pattern for the `regex` version source

### [0.7.0](https://github.com/ofek/hatch/releases/tag/hatchling-v0.7.0) - 2022-01-08 ### {: #hatchling-v0.7.0 }

***Added:***

- Improve default file selection to account for `src`-layout structures and namespaced packages

***Fixed:***

- The normalization of project versions no longer strips trailing zero release segments

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
