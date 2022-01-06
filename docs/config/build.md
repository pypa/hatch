# Build configuration

-----

All build configuration is defined in the `tool.hatch.build` table.

[Build targets](#build-targets) are defined as sections within `tool.hatch.build.targets`:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.<TARGET_NAME>]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.<TARGET_NAME>]
    ```

For each build target you may override any of the defaults set in the top-level `tool.hatch.build` table.

## Build system

To be compatible with the broader [Python packaging ecosystem](../build.md#packaging-ecosystem), you must define the [build system](https://www.python.org/dev/peps/pep-0517/#source-trees) as follows:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"
    ```

The version of `hatchling` defined here will be used to build all targets.

Hatchling is a [PEP 517][]/[PEP 660][] compatible build system and is a dependency of Hatch itself.

## File selection

### VCS

By default, Hatch will respect any `.gitignore` file located at your project's root. Set `ignore-vcs` to `true` to disable this behavior:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build]
    ignore-vcs = true
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build]
    ignore-vcs = true
    ```

### Patterns

You can set the `include` and `exclude` options to select exactly which files will be shipped in each build, with `exclude` taking precedence. Every entry represents a [Git-style glob pattern](https://git-scm.com/docs/gitignore#_pattern_format).

For example, the following configuration:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build]
    include = [
      "pkg/*.py",
      "/tests",
    ]
    exclude = [
      "*.json",
      "pkg/_compat.py",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build]
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

### Packages

The `packages` option can be used to include specific Python packages. This option is semantically equivalent to `include` except that every entry is a simple relative path and the shipped path will be collapsed to only include the final component.

So for example, if you want to ship a package `foo` that is stored in a directory `src` you would do:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.wheel]
    packages = ["src/foo"]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.wheel]
    packages = ["src/foo"]
    ```

### Artifacts

If you want to include files that are [ignored by your VCS](#vcs), such as those that might be created by [build hooks](#build-hooks), you can use the `artifacts` option. This option is semantically equivalent to `include`.

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build]
    artifacts = [
      "*.so",
      "*.dll",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build]
    artifacts = [
      "*.so",
      "*.dll",
    ]
    ```

### Default file selection

If no file selection options are provided, then what gets included is determined by each [build target](#build-targets).

## Reproducible builds

By default, [build targets](#build-targets) will build in a reproducible manner provided that they support that behavior. To disable this, set `reproducible` to `false`:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build]
    reproducible = false
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build]
    reproducible = false
    ```

When enabled, the [SOURCE_DATE_EPOCH](https://reproducible-builds.org/specs/source-date-epoch/) environment variable will be used for all build timestamps. If not set, then Hatch will use an [unchanging default value](../plugins/utilities.md#hatchling.builders.utils.get_reproducible_timestamp).

## Output directory

When the output directory is not provided to the [`build`](../cli/reference.md#hatch-build) command, the `dist` directory will be used by default. You can change the default to a different directory using a relative or absolute path like so:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build]
    directory = "<PATH>"
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build]
    directory = "<PATH>"
    ```

## Dev mode

In most cases, [dev mode](environment.md#dev-mode) environment installations or [editable installs](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs) in general will work as expected. However, for some project layouts you need to explicitly define which directories to add to Python's search path, such as for [namespace packages](https://packaging.python.org/guides/packaging-namespace-packages/).

You can do this with the `dev-mode-dirs` option:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build]
    dev-mode-dirs = ["."]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build]
    dev-mode-dirs = ["."]
    ```

## Build targets

A build target can be provided by any [builder plugin](../plugins/builder.md). There are three built-in build targets: [wheel](../plugins/builder.md#wheel), [sdist](../plugins/builder.md#source-distribution), and [custom](../plugins/builder.md#custom).

### Dependencies

You can specify additional dependencies that will be installed in each build environment, such as for third party builders:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.your-target-name]
    dependencies = [
      "your-builder-plugin"
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.your-target-name]
    dependencies = [
      "your-builder-plugin"
    ]
    ```

### Versions

If a build target supports multiple build strategies or if there are major changes over time, you can specify exactly which versions you want to build using the `versions` option, which may be defined as either an array of strings or a comma-separated string:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.<TARGET_NAME>]
    versions = [
      "v1",
      "beta-feature",
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.<TARGET_NAME>]
    versions = [
      "v1",
      "beta-feature",
    ]
    ```

## Build hooks

A build hook defines code that will be executed at various stages of the build process and can be provided by any [build hook plugin](../plugins/build-hook.md). There is one built-in build hook: [custom](../plugins/build-hook.md#custom).

Build hooks can be applied either globally:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.hooks.<HOOK_NAME>]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.hooks.<HOOK_NAME>]
    ```

or to specific build targets:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.targets.<TARGET_NAME>.hooks.<HOOK_NAME>]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.targets.<TARGET_NAME>.hooks.<HOOK_NAME>]
    ```

### Dependencies

You can specify additional dependencies that will be installed in each build environment, such as for third party build hooks:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.hooks.your-hook-name]
    dependencies = [
      "your-build-hook-plugin"
    ]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.hooks.your-hook-name]
    dependencies = [
      "your-build-hook-plugin"
    ]
    ```

### Order of execution

For each build target, build hooks execute in the order in which they are defined, starting with target-specific hooks.

As an example, for the following configuration:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.hooks.hook3]
    [tool.hatch.build.hooks.hook1]

    [tool.hatch.build.targets.foo.hooks.hook2]
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.hooks.hook3]
    [build.hooks.hook1]

    [build.targets.foo.hooks.hook2]
    ```

When target `foo` is built, build hook `hook2` will be executed first, followed by `hook3`, and then finally `hook1`.

### Conditional execution

If you want to disable a build hook by default and control its use by [environment variables](#environment-variables), you can do so by setting the `enable-by-default` option to `false`:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.hatch.build.hooks.<HOOK_NAME>]
    enable-by-default = false
    ```

=== ":octicons-file-code-16: hatch.toml"

    ```toml
    [build.hooks.<HOOK_NAME>]
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
| `HATCH_BUILD_HOOK_ENABLE_<HOOK_NAME>` | `false` |  |
| `HATCH_BUILD_LOCATION` | `dist` | The location with which to build the targets; only used by the [`build`](../cli/reference.md#hatch-build) command |
