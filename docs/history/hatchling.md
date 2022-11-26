# Hatchling history

-----

All notable changes to Hatchling will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

***Added:***

- Add `extra_metadata` build data to the `wheel` target
- Retroactively support `License-Expression` core metadata starting at version 2.1
- Add more type hints
- Store Hatchling's metadata in `pyproject.toml`

## [1.11.1](https://github.com/pypa/hatch/releases/tag/hatchling-v1.11.1) - 2022-10-19 ## {: #hatchling-v1.11.1 }

***Fixed:***

- Fix default file selection behavior of the `wheel` target when there is a single top-level module

## [1.11.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.11.0) - 2022-10-08 ## {: #hatchling-v1.11.0 }

***Added:***

- Add `env` version source to retrieve the version from an environment variable
- Add `validate-bump` option to the `standard` version scheme

***Fixed:***

- Use proper CSV formatting for the `RECORD` metadata file of the `wheel` target to avoid warnings during installation by `pip` if, for example, file names contain commas
- Fix installations with pip for build hooks that modify runtime dependencies
- Decreasing verbosity now has no affect on output that should always be displayed

## [1.10.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.10.0) - 2022-09-18 ## {: #hatchling-v1.10.0 }

***Added:***

- Add the following to the list of directories that cannot be traversed: `__pypackages__`, `.hg`, `.hatch`, `.tox`, `.nox`
- Add deprecated option to allow ambiguous features

***Fixed:***

- Improve tracking of dynamic metadata
- Fix core metadata for entries in `project.optional-dependencies` that use direct references

## [1.9.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.9.0) - 2022-09-09 ## {: #hatchling-v1.9.0 }

***Changed:***

- File pattern matching now more closely resembles Git's behavior

***Added:***

- Implement a minimal version of `prepare_metadata_for_build_wheel` and `prepare_metadata_for_build_editable` for non-frontend tools that only need to inspect a project's metadata
- Add `metadata` command to view PEP 621 project metadata
- Improve error messages for SPDX license errors
- Retroactively support `License-File` for core metadata starting at version 2.1
- Bump the minimum supported version of `pathspec` to 0.10.1

***Fixed:***

- Allow the valid non-SPDX `license` values `LicenseRef-Public-Domain` and `LicenseRef-Proprietary`
- Show the help text of the CLI when no subcommand is selected

## [1.8.1](https://github.com/pypa/hatch/releases/tag/hatchling-v1.8.1) - 2022-08-25 ## {: #hatchling-v1.8.1 }

***Fixed:***

- Fix default file inclusion for `wheel` build targets when both the project name and package directory name are not normalized

## [1.8.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.8.0) - 2022-08-16 ## {: #hatchling-v1.8.0 }

***Added:***

- Add `get_known_classifiers` method to metadata hooks

***Fixed:***

- Fix check for updating static versions with the `version` command when metadata hooks are in use

## [1.7.1](https://github.com/pypa/hatch/releases/tag/hatchling-v1.7.1) - 2022-08-13 ## {: #hatchling-v1.7.1 }

***Fixed:***

- Fix the value of the `relative_path` attribute of included files, that some build plugins may use, when selecting explicit paths

## [1.7.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.7.0) - 2022-08-12 ## {: #hatchling-v1.7.0 }

***Added:***

- Add `require-runtime-features` option for builders and build hooks
- Check for unknown trove classifiers
- Update SPDX license information to version 3.18

***Fixed:***

- Add better error message for `wheel` target dev mode installations that define path rewrites with the `sources` option
- Note the `allow-direct-references` option in the relevant error messages

## [1.6.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.6.0) - 2022-07-23 ## {: #hatchling-v1.6.0 }

***Changed:***

- When no build targets are specified on the command line, now default to `sdist` and `wheel` targets rather than what happens to be defined in config
- The `code` version source now only supports files with known extensions
- Global build hooks now run before target-specific build hooks to better match expected behavior

***Added:***

- The `code` version source now supports loading extension modules
- Add `search-paths` option for the `code` version source

***Fixed:***

- Fix removing `sources` using an empty string value in the mapping
- The `strict-naming` option now also applies to the metadata directory of `wheel` targets

## [1.5.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.5.0) - 2022-07-11 ## {: #hatchling-v1.5.0 }

***Added:***

- Support the final draft of PEP 639
- Add `strict-naming` option for `sdist` and `wheel` targets

***Fixed:***

- Project names are now stored in `sdist` and `wheel` target core metadata exactly as defined in `pyproject.toml` without normalization to allow control of how PyPI displays them

## [1.4.1](https://github.com/pypa/hatch/releases/tag/hatchling-v1.4.1) - 2022-07-04 ## {: #hatchling-v1.4.1 }

***Fixed:***

- Fix forced inclusion of important files like licenses for `sdist` targets when using the explicit selection options
- Don't sort project URL metadata so that the rendered order on PyPI can be controlled

## [1.4.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.4.0) - 2022-07-03 ## {: #hatchling-v1.4.0 }

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

## [1.3.1](https://github.com/pypa/hatch/releases/tag/hatchling-v1.3.1) - 2022-05-30 ## {: #hatchling-v1.3.1 }

***Fixed:***

- Better populate global variables for the `code` version source

## [1.3.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.3.0) - 2022-05-22 ## {: #hatchling-v1.3.0 }

***Removed:***

- Remove unused global `args` context string formatting field

***Added:***

- Improve error messages for the `env` context string formatting field

***Fixed:***

- Fix `uri` context string formatting modifier on Windows

## [1.2.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.2.0) - 2022-05-20 ## {: #hatchling-v1.2.0 }

***Added:***

- Allow context formatting for `project.dependencies` and `project.optional-dependencies`

## [1.1.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.1.0) - 2022-05-19 ## {: #hatchling-v1.1.0 }

***Added:***

- Add `uri` and `real` context string formatting modifiers for file system paths

## [1.0.0](https://github.com/pypa/hatch/releases/tag/hatchling-v1.0.0) - 2022-05-17 ## {: #hatchling-v1.0.0 }

***Changed:***

- Drop support for Python 2

***Added:***

- Improve error messaging for invalid versions
- Update project metadata to reflect support for Python 3.11

## [0.25.1](https://github.com/pypa/hatch/releases/tag/hatchling-v0.25.1) - 2022-06-14 ## {: #hatchling-v0.25.1 }

***Fixed:***

- Fix support for Windows on Python 2 by removing its support for symlinks

## [0.25.0](https://github.com/pypa/hatch/releases/tag/hatchling-v0.25.0) - 2022-05-15 ## {: #hatchling-v0.25.0 }

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

## [0.24.0](https://github.com/pypa/hatch/releases/tag/hatchling-v0.24.0) - 2022-04-28 ## {: #hatchling-v0.24.0 }

This is the initial public release of the Hatchling build system. Support for Python 2 will be dropped in version 1.
