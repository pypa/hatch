# How to use lockfiles

-----

Hatch can generate [PEP 751](https://peps.python.org/pep-0751/) lockfiles (`pylock.toml`) for your environments. Lockfiles capture the exact resolved versions and hashes of all dependencies, ensuring reproducible installations across machines and CI.

## Locking a specific environment

Use the [`env lock`](../../cli/reference.md#hatch-env-lock) command with an environment name to generate a lockfile:

```console
$ hatch env lock test
Locking environment: test
Wrote lockfile: /path/to/project/pylock.test.toml
```

The `default` environment produces `pylock.toml`, while all other environments produce `pylock.<ENV_NAME>.toml`, following the [PEP 751](https://peps.python.org/pep-0751/) naming convention.

## Locking all environments

To lock every environment at once, use the `--all` flag:

```console
$ hatch env lock --all
```

Environments that are incompatible with the current platform (e.g. a matrix variant requiring a Python version that is not installed) will be skipped with a warning.

## Automatic locking

You can configure environments to generate lockfiles automatically whenever they are created or their dependencies change. Set [`locked`](../../config/environment/overview.md#locked) to `true` on individual environments:

```toml config-example
[tool.hatch.envs.test]
locked = true
dependencies = [
  "pytest",
]
```

Or enable it for all environments at once with the global [`lock-envs`](../../config/environment/overview.md#lock-envs) setting:

```toml config-example
[tool.hatch]
lock-envs = true
```

Individual environments can opt out of the global setting:

```toml config-example
[tool.hatch]
lock-envs = true

[tool.hatch.envs.docs]
locked = false
```

When no explicit environment name is passed, `hatch env lock` will lock all environments that have `locked = true` (either directly or via the global setting).

## Updating locked dependencies

To upgrade all locked packages to their latest allowed versions:

```console
$ hatch env lock test --upgrade
```

To upgrade only specific packages:

```console
$ hatch env lock test --upgrade-package requests --upgrade-package urllib3
```

## Checking if a lockfile is up-to-date

Use the `--check` flag to verify that a lockfile exists without regenerating it:

```console
$ hatch env lock test --check
Lockfile exists: /path/to/project/pylock.test.toml
```

This is useful in CI to ensure lockfiles have been committed.

## Exporting to a custom path

By default, lockfiles are written to the project root. Use `--export` to write to a different location:

```console
$ hatch env lock test --export locks/test.lock
```

## Custom lock filenames

You can override the default filename for any environment with the [`lock-filename`](../../config/environment/overview.md#lock-filename) option:

```toml config-example
[tool.hatch.envs.test]
lock-filename = "requirements-test.lock"
```

## Installer integration

Lockfile generation delegates to whichever installer your environment is configured to use:

- **pip** (default): Uses `pip lock` (requires pip 25.1+) to produce a `pylock.toml` file directly.
- **UV**: Uses `uv pip compile` to resolve dependencies with hashes.

See [How to select the installer](select-installer.md) for details on configuring UV.
