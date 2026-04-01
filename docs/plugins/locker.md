# Dependency locker plugins

-----

Hatch selects a **locker** plugin to **generate** PEP 751 lockfiles, verify they are **in sync** with the configured dependency inputs, and **apply** them when syncing a `locked` environment. Built-in lockers are **`uv`** and **`pip`**, matching the [virtual environment installer](../how-to/environment/select-installer.md).

This design follows [Environment dependency locking (#355)](https://github.com/pypa/hatch/discussions/355): lockers use the environment’s **public** API (for example [`command_context`](../plugins/environment/reference.md#hatch.env.plugin.interface.EnvironmentInterface.command_context) and [`platform`](../plugins/utilities.md)) instead of subclassing [`EnvironmentInterface`](../plugins/environment/reference.md).

## Registration

```python tab="hooks.py"
from hatchling.plugin import hookimpl

from .locker import MyLocker


@hookimpl
def hatch_register_locker():
    return MyLocker
```

Expose the module on the `hatch` entry point (see [Plugins — Discovery](about.md#discovery)) and list the distribution under [`tool.hatch.env.requires`](../config/hatch.md#environment) when the plugin is not installed globally.

## Interface

Implement [`LockerInterface`](https://github.com/pypa/hatch/blob/master/src/hatch/env/lockers/interface.py) with:

- `PLUGIN_NAME: str` — selector (`uv`, `pip`, or your plugin name).
- `supports(environment) -> bool`
- `generate(environment, dependencies: list[str], output_path, *, upgrade=..., layered=..., lock_extras=..., lock_groups=..., upgrade_packages=...)`
- `in_sync(environment, dependencies: list[str], output_path, *, same flags as generate) -> bool`
- `apply_lock(environment, lock_path)`
- Optional override: `install_matches_lock(environment, lock_path) -> bool` for `dependencies_in_sync` when `locked` (default `True`; UV uses `uv pip sync --dry-run`).

## Mapping from discussion #355

| #355 sketch | Hatch |
| ----------- | ----- |
| `generate(dependencies: list[str])` → resolve → persist | `generate(environment, dependencies, output_path, *, …)` — orchestrator supplies merged PEP 508 lines plus layered flags (`lock_extras`, `lock_groups`, `upgrade`, …). |
| `in_sync(dependencies) -> bool` | `in_sync(environment, dependencies, output_path, *, …) -> bool` |
| `write_file` / `read_file` on the environment | Lockfiles normally live on the project root: read/write `output_path` ([`Path`](../plugins/utilities.md)). For remote or isolated storage, use [`fs_context`](../plugins/environment/reference.md#hatch.env.plugin.interface.EnvironmentInterface.fs_context) to stage paths and `sync_local` / `sync_env` before or after resolver commands. |
| `run_shell_command` under `command_context` | Run resolver/install commands inside `with environment.command_context():` using `environment.platform.check_command` / `run_command` (same pattern as built-in lockers). |
| *(not in 2022 snippet)* apply install graph | `apply_lock(environment, lock_path)` — e.g. `uv pip sync` for the UV locker. |

## Configuration

- Global default: [`tool.hatch.locker`](../config/environment/overview.md#locker) (string plugin name).
- Per environment: [`tool.hatch.envs.<name>.locker`](../config/environment/overview.md#locker) overrides the global value.
- If unset, Hatch picks `uv` when the environment uses the UV installer, otherwise `pip`.

## Built-in lockers

| `PLUGIN_NAME` | When selected | Notes |
| ------------- | ------------- | ----- |
| `uv` | Virtual env + UV installer | `uv pip compile` / `uv pip sync`; supports layered locks (extras, dependency-groups, `pyproject.toml`). |
| `pip` | Any supported environment | `pip lock`; flat dependency list only (no layered extras/groups in the pip locker). `apply_lock` is a no-op — use UV for `locked` installs from a pylock today. |
