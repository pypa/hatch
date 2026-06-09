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

### `hatch env lock` (all or named environments)

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

### `hatch dep lock` and `hatch lock` (active environment)

For the environment selected with `-e` / `HATCH_ENV` (see the [CLI](../../cli/about.md)), you can run:

- [`dep lock`](../../cli/reference.md#hatch-dep-lock) — same resolver options as `env lock` where applicable (`--upgrade`, `--upgrade-package`, `--export`, `--export-all`, `--check`).
- [`lock`](../../cli/reference.md#hatch-lock) — shorthand for `hatch dep lock`.

Matrix parents and other names still expand the same way as elsewhere; `--export-all` locks every configured environment into a directory, matching `hatch env lock --export-all`.

## Syncing from a lockfile

[`dep sync`](../../cli/reference.md#hatch-dep-sync) runs the selected locker’s **`apply_lock`** step for the active environment (for example `uv pip sync` when using the UV locker). The environment must be [`locked`](../../config/environment/overview.md#locked) and the lockfile must already exist—run `hatch dep lock` or `hatch env lock` first.

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

Use `--check` on `hatch env lock`, `hatch dep lock`, or `hatch lock` to verify the lockfile is **in sync** with the current dependency inputs (re-resolve and compare). If there is nothing to lock for that environment, Hatch only checks that the file exists.

```console
$ hatch env lock test --check
Lockfile is up to date: /path/to/project/pylock.test.toml
```

This is useful in CI to ensure lockfiles have been committed and match `pyproject.toml` / env dependencies.

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

## Installer integration and locker selection

By default, Hatch picks a built-in **locker** from the environment installer:

- **pip** (default): `pip lock` (requires pip 25.1+) for generation.
- **UV**: `uv pip compile` (with hashes) and `uv pip sync` when applying a lock.

Override with [`tool.hatch.locker`](../../config/environment/overview.md#locker) or [`tool.hatch.envs.<name>.locker`](../../config/environment/overview.md#locker). See [Dependency locker plugins](../../plugins/locker.md) to implement `hatch_register_locker`.

See [Dependency locker plugins](../../plugins/locker.md) for the full plugin interface.
