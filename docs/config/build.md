# Build configuration

-----

[Build targets](#build-targets) are defined as sections within `tool.hatch.build.targets`:

```toml config-example
[tool.hatch.build.targets.<TARGET_NAME>]
```

!!! tip
    Although not recommended, you may define global configuration in the `tool.hatch.build` table. Keys may then be overridden by target config.

## Build system

To be compatible with the broader [Python packaging ecosystem](../build.md#packaging-ecosystem), you must define the [build system](https://peps.python.org/pep-0517/#source-trees) as follows:

```toml tab="pyproject.toml"
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

The version of `hatchling` defined here will be used to build all targets.

Hatchling is a standards-compliant[^1] build backend and is a dependency of Hatch itself.

## File selection

### VCS

By default, Hatch will respect the first `.gitignore` or `.hgignore` file found in your project's root directory or parent directories. Set `ignore-vcs` to `true` to disable this behavior:

```toml config-example
[tool.hatch.build.targets.sdist]
ignore-vcs = true
```

!!! note
    For `.hgignore` files only glob syntax is supported.

### Patterns

You can set the `include` and `exclude` options to select exactly which files will be shipped in each build, with `exclude` taking precedence. Every entry represents a [Git-style glob pattern](https://git-scm.com/docs/gitignore#_pattern_format).

For example, the following configuration:

```toml config-example
[tool.hatch.build.targets.sdist]
include = [
  "pkg/*.py",
  "/tests",
]
exclude = [
  "*.json",
  "pkg/_compat.py",
]
```

will exclude every file with a `.json` extension, and will include everything under a `tests` directory located at the root and every file with a `.py` extension that is directly under a `pkg` directory located at the root except for `_compat.py`.

### Artifacts

If you want to include files that are [ignored by your VCS](#vcs), such as those that might be created by [build hooks](#build-hooks), you can use the `artifacts` option. This option is semantically equivalent to `include`.

Note that artifacts are not affected by the `exclude` option. Artifacts can
be excluded by using more explicit paths or by using the `!` negation operator.
When using the `!` operator, the negated pattern(s) must come after the more
generic ones.

```toml config-example
[tool.hatch.build.targets.wheel]
artifacts = [
  "*.so",
  "*.dll",
  "!/foo/*.so",
]
```

### Explicit selection

#### Generic

You can use the `only-include` option to prevent directory traversal starting at the project root and only select specific relative paths to directories or files. Using this option ignores any defined [`include` patterns](#patterns).

```toml config-example
[tool.hatch.build.targets.sdist]
only-include = ["pkg", "tests/unit"]
```

#### Packages

The `packages` option is semantically equivalent to `only-include` (which takes precedence) except that the shipped path will be collapsed to only include the final component.

So for example, if you want to ship a package `foo` that is stored in a directory `src` you would do:

```toml config-example
[tool.hatch.build.targets.wheel]
packages = ["src/foo"]
```

### Forced inclusion

The `force-include` option allows you to select specific files or directories from anywhere on the file system that should be included and map them to the desired relative distribution path.

For example, if there was a directory alongside the project root named `artifacts` containing a file named `lib.so` and a file named `lib.h` in your home directory, you could ship both files in a `pkg` directory with the following configuration:

```toml config-example
[tool.hatch.build.targets.wheel.force-include]
"../artifacts" = "pkg"
"~/lib.h" = "pkg/lib.h"
```

!!! note
    - Files must be mapped exactly to their desired paths, not to directories.
    - The contents of directory sources are recursively included.
    - To map directory contents directly to the root use `/` (a forward slash).
    - Sources that do not exist will raise an error.

!!! warning
    Files included using this option will overwrite any file path that was already included by other file selection options.

### Default file selection

If no file selection options are provided, then what gets included is determined by each [build target](#build-targets).

### Excluding files outside packages

If you want to exclude non-[artifact](#artifacts) files that do not reside within a Python package, set `only-packages` to `true`:

```toml config-example
[tool.hatch.build.targets.wheel]
only-packages = true
```

### Rewriting paths

You can rewrite relative paths to directories with the `sources` option. For example, the following configuration:

```toml config-example
[tool.hatch.build.targets.wheel.sources]
"src/foo" = "bar"
```

would distribute the file `src/foo/file.ext` as `bar/file.ext`.

If you want to remove path prefixes entirely, rather than setting each to an empty string, you can define `sources` as an array:

```toml config-example
[tool.hatch.build.targets.wheel]
sources = ["src"]
```

If you want to add a prefix to paths, you can use an empty string. For example, the following configuration:

```toml config-example
[tool.hatch.build.targets.wheel.sources]
"" = "foo"
```

would distribute the file `bar/file.ext` as `foo/bar/file.ext`.

The [packages](#packages) option itself relies on sources. Defining `#!toml packages = ["src/foo"]` for the `wheel` target is equivalent to the following:

```toml config-example
[tool.hatch.build.targets.wheel]
only-include = ["src/foo"]
sources = ["src"]
```

### Performance

All encountered directories are traversed by default. To skip non-[artifact](#artifacts) directories that are excluded, set `skip-excluded-dirs` to `true`:

```toml config-example
[tool.hatch.build]
skip-excluded-dirs = true
```

!!! warning
    This may result in not shipping desired files. For example, if you want to include the file `a/b/c.txt` but your [VCS ignores](#vcs) `a/b`, the file `c.txt` will not be seen because its parent directory will not be entered. In such cases you can use the [`force-include`](#forced-inclusion) option.

## Reproducible builds

By default, [build targets](#build-targets) will build in a reproducible manner provided that they support that behavior. To disable this, set `reproducible` to `false`:

```toml config-example
[tool.hatch.build]
reproducible = false
```

When enabled, the [SOURCE_DATE_EPOCH](https://reproducible-builds.org/specs/source-date-epoch/) environment variable will be used for all build timestamps. If not set, then Hatch will use an [unchanging default value](../plugins/utilities.md#hatchling.builders.utils.get_reproducible_timestamp).

## Output directory

When the output directory is not provided to the [`build`](../cli/reference.md#hatch-build) command, the `dist` directory will be used by default. You can change the default to a different directory using a relative or absolute path like so:

```toml config-example
[tool.hatch.build]
directory = "<PATH>"
```

## Dev mode

By default for [dev mode](environment/overview.md#dev-mode) environment installations or [editable installs](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs), the `wheel` target will determine which directories should be added to Python's search path based on the [selected files](#file-selection).

If you want to override this detection or perhaps instruct other build targets as well, you can use the `dev-mode-dirs` option:

```toml config-example
[tool.hatch.build]
dev-mode-dirs = ["."]
```

If you don't want to add entire directories to Python's search path, you can enable a more targeted mechanism with the mutually exclusive `dev-mode-exact` option:

```toml config-example
[tool.hatch.build]
dev-mode-exact = true
```

!!! warning
    The `dev-mode-exact` mechanism is [not supported](https://github.com/microsoft/pylance-release/issues/2114) by static analysis tools & IDEs, therefore functionality such as autocompletion is unlikely to work.

## Build targets

A build target can be provided by any [builder plugin](../plugins/builder/reference.md). There are three built-in build targets: [wheel](../plugins/builder/wheel.md), [sdist](../plugins/builder/sdist.md), and [custom](../plugins/builder/custom.md).

### Dependencies

You can specify additional dependencies that will be installed in each build environment, such as for third party builders:

```toml config-example
[tool.hatch.build.targets.your-target-name]
dependencies = [
  "your-builder-plugin"
]
```

You can also declare dependence on the project's [runtime dependencies](metadata.md#required) with the `require-runtime-dependencies` option:

```toml config-example
[tool.hatch.build.targets.your-target-name]
require-runtime-dependencies = true
```

Additionally, you may declare dependence on specific [runtime features](metadata.md#optional) of the project with the `require-runtime-features` option:

```toml config-example
[tool.hatch.build.targets.your-target-name]
require-runtime-features = [
  "feature1",
  "feature2",
]
```

### Versions

If a build target supports multiple build strategies or if there are major changes over time, you can specify exactly which versions you want to build using the `versions` option:

```toml config-example
[tool.hatch.build.targets.<TARGET_NAME>]
versions = [
  "v1",
  "beta-feature",
]
```

See the [wheel](../plugins/builder/wheel.md#versions) target for a real world example.

## Build hooks

A build hook defines code that will be executed at various stages of the build process and can be provided by any [build hook plugin](../plugins/build-hook/reference.md). There is one built-in build hook: [custom](../plugins/build-hook/custom.md).

Build hooks can be applied either globally:

```toml config-example
[tool.hatch.build.hooks.<HOOK_NAME>]
```

or to specific build targets:

```toml config-example
[tool.hatch.build.targets.<TARGET_NAME>.hooks.<HOOK_NAME>]
```

### Dependencies

You can specify additional dependencies that will be installed in each build environment, such as for third party build hooks:

```toml config-example
[tool.hatch.build.hooks.your-hook-name]
dependencies = [
  "your-build-hook-plugin"
]
```

You can also declare dependence on the project's [runtime dependencies](metadata.md#required) with the `require-runtime-dependencies` option:

```toml config-example
[tool.hatch.build.hooks.your-hook-name]
require-runtime-dependencies = true
```

Additionally, you may declare dependence on specific [runtime features](metadata.md#optional) of the project with the `require-runtime-features` option:

```toml config-example
[tool.hatch.build.hooks.your-hook-name]
require-runtime-features = [
  "feature1",
  "feature2",
]
```

### Order of execution

For each build target, build hooks execute in the order in which they are defined, starting with global hooks.

As an example, for the following configuration:

```toml config-example
[tool.hatch.build.targets.foo.hooks.hook2]

[tool.hatch.build.hooks.hook3]
[tool.hatch.build.hooks.hook1]
```

When target `foo` is built, build hook `hook3` will be executed first, followed by `hook1`, and then finally `hook2`.

### Conditional execution

If you want to disable a build hook by default and control its use by [environment variables](#environment-variables), you can do so by setting the `enable-by-default` option to `false`:

```toml config-example
[tool.hatch.build.hooks.<HOOK_NAME>]
enable-by-default = false
```

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `HATCH_BUILD_CLEAN` | `false` | Whether or not existing artifacts should first be removed |
| `HATCH_BUILD_CLEAN_HOOKS_AFTER` | `false` | Whether or not build hook artifacts should be removed after each build |
| `HATCH_BUILD_HOOKS_ONLY` | `false` | Whether or not to only execute build hooks |
| `HATCH_BUILD_NO_HOOKS` | `false` | Whether or not to disable all build hooks; this takes precedence over other options |
| `HATCH_BUILD_HOOKS_ENABLE` | `false` | Whether or not to enable all build hooks |
| `HATCH_BUILD_HOOK_ENABLE_<HOOK_NAME>` | `false` | Whether or not to enable the build hook named `<HOOK_NAME>` |
| `HATCH_BUILD_LOCATION` | `dist` | The location with which to build the targets; only used by the [`build`](../cli/reference.md#hatch-build) command |

[^1]: Support for [PEP 517][] and [PEP 660][] guarantees interoperability with other build tools.
