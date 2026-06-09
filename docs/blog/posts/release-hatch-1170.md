---
date: 2026-05-30
authors: [cjames23]
description: >-
  Hatch v1.17.0 brings lockfile support and a new unified check command.
categories:
  - Release
---

# Hatch v1.17.0

Hatch [v1.17.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.17.0) brings first-class lockfile support and a new `hatch check` command that unifies code quality checks under a single, extensible interface.

<!-- more -->

## Lockfile support

 Hatch now generates [PEP 751](https://peps.python.org/pep-0751/) lockfiles (`pylock.toml`) for your environments, capturing exact resolved versions and cryptographic hashes of every dependency.

### Getting started

Enable locking on any environment:

```toml config-example
[tool.hatch.envs.test]
locked = true
dependencies = [
  "pytest",
]
```

Or flip it on globally:

```toml config-example
[tool.hatch]
lock-envs = true
```

Then generate lockfiles:

```console
$ hatch env lock
Locking environment: default
Wrote lockfile: pylock.toml
Locking environment: test
Wrote lockfile: pylock.test.toml
```

The `default` environment produces `pylock.toml`, while others follow the `pylock.<name>.toml` convention from PEP 751.

### Automatic locking

Environments configured with `locked = true` will have their lockfiles generated automatically during `hatch env create` or `hatch run` whenever the lockfile is missing or dependencies have changed. No extra steps required.

### CI verification

Use `--check` to verify lockfiles are up to date in CI pipelines:

```console
$ hatch env lock --check
Lockfile is up to date: pylock.toml
```

This re-resolves dependencies and compares the result against the committed lockfile, failing if they diverge.

### Upgrading dependencies

Upgrade everything:

```console
$ hatch env lock --upgrade
```

Or target specific packages:

```console
$ hatch env lock --upgrade-package requests --upgrade-package urllib3
```

### Pluggable lockers

The lockfile system is built on a plugin interface. Hatch ships two built-in lockers:

- **UV** — uses `uv pip compile` with hash generation and `uv pip sync` for installation
- **pip** — uses `pip lock` (requires pip 25.1+)

The locker is selected automatically based on your environment's installer, or you can set it explicitly:

```toml config-example
[tool.hatch]
locker = "uv"
```

Third-party locker plugins can be registered via the `hatch_register_locker` hook, implementing the `LockerInterface` to provide custom resolution strategies.

### Additional commands

- `hatch lock` — shorthand for locking the active environment
- `hatch dep lock` — same workflow, scoped to the `-e` / `HATCH_ENV` selection
- `hatch dep sync` — install from an existing lockfile (e.g. `uv pip sync`)
- `--export` / `--export-all` — write lockfiles to custom paths or export all environments to a directory

## The `hatch check` command

The new [`check`](../../cli/reference.md#hatch-check) command brings linting, formatting verification, and type checking together under one roof:

```console
$ hatch check
```

That single invocation runs all three checks in sequence. You can also target individual checks:

```console
$ hatch check code    # static analysis (Ruff linter)
$ hatch check fmt     # formatting verification (Ruff formatter)
$ hatch check types   # type checking (Pyrefly)
```

Add `--fix` to automatically apply fixes for code and formatting issues:

```console
$ hatch check --fix
```

### Type checking with Pyrefly

The `types` subcommand uses [Pyrefly](https://github.com/facebook/pyrefly) by default, bringing fast, incremental type checking to your workflow. It also supports `--cover` for type coverage reports and `--summarize` for error statistics.

### Designed for extensibility

The architecture behind `hatch check` is deliberately modular. Each subcommand (`code`, `fmt`, `types`) runs in its own dedicated managed environment (`hatch-check-code`, `hatch-check-fmt`, `hatch-check-types`), with its own scripts and configuration.

This design sets the stage for extreme extensibility in future releases. The same pattern that lets Hatch manage Ruff and Pyrefly today will allow users to plug in their own checkers — security scanners, documentation linters, custom style enforcers, license auditors — as first-class `hatch check` subcommands. Each checker will be able to define its own environment, dependencies, and scripts, all orchestrated through the same unified interface.

We are building toward a world where `hatch check` becomes the single entry point for every quality gate your project needs, with the plugin system handling the rest.


### Support

If you or your organization finds value in what Hatch provides, consider sponsoring our maintainers [Ofek](https://github.com/sponsors/ofek)[Cary](https://github.com/sponsors/cjames23) to assist with maintenance and more rapid development!
