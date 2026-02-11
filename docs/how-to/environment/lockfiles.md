# How to use lockfiles

-----

Hatch can generate [PEP 751](https://peps.python.org/pep-0751/) lockfiles (`pylock.toml`) for your environments. Lockfiles capture the exact resolved versions and hashes of all dependencies, ensuring reproducible installations across machines and CI.

## Configuring locked environments

To use lockfiles, first configure which environments should be locked by setting [`locked = true`](../../config/environment/overview.md#locked):

```toml config-example
[tool.hatch.envs.test]
locked = true
dependencies = [
  "pytest",
]
```

Or enable it globally for all environments with the [`lock-envs`](../../config/environment/overview.md#lock-envs) setting:

```toml config-example
[tool.hatch]
lock-envs = true
```

Individual environments can opt out:

```toml config-example
[tool.hatch]
lock-envs = true

[tool.hatch.envs.docs]
locked = false
```

## Generating lockfiles

Use the [`env lock`](../../cli/reference.md#hatch-env-lock) command to generate lockfiles. When called without arguments, it locks all environments configured with `locked = true`:

```console
$ hatch env lock
Locking environment: default
Wrote lockfile: /path/to/project/pylock.toml
Locking environment: test
Wrote lockfile: /path/to/project/pylock.test.toml
```

You can also lock a specific environment by name:

```console
$ hatch env lock test
Locking environment: test
Wrote lockfile: /path/to/project/pylock.test.toml
```

!!! note
    When locking a specific environment by name, it must have `locked = true` configured. To generate a lockfile for an environment that is not configured as locked, use the `--export` flag.

The `default` environment produces `pylock.toml`, while all other environments produce `pylock.<ENV_NAME>.toml`, following the [PEP 751](https://peps.python.org/pep-0751/) naming convention.

## Automatic locking

Environments with `locked = true` will have their lockfiles generated automatically during `hatch env create` or `hatch run` whenever:

- The lockfile does not exist yet
- The environment's dependencies have changed

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

## Exporting lockfiles

To generate a lockfile for an environment that is not configured with `locked = true`, or to write to a custom location, use `--export`:

```console
$ hatch env lock default --export locks/default.lock
```

To export lockfiles for all environments into a directory, use `--export-all`:

```console
$ hatch env lock --export-all locks/
```

!!! note
    `--export` and `--export-all` are mutually exclusive.

## Custom lock filenames

You can override the default filename for any environment with the [`lock-filename`](../../config/environment/overview.md#lock-filename) option:

```toml config-example
[tool.hatch.envs.test]
lock-filename = "requirements-test.lock"
```

When multiple matrix environments share the same `lock-filename`, Hatch will merge their dependencies and generate the lockfile once.

## Installer integration

Lockfile generation delegates to whichever installer your environment is configured to use:

- **pip** (default): Uses `pip lock` (requires pip 25.1+) to produce a `pylock.toml` file directly.
- **UV**: Uses `uv pip compile` to resolve dependencies with hashes.

See [How to select the installer](select-installer.md) for details on configuring UV.
