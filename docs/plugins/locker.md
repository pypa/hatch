# Dependency locker plugins

-----

Hatch selects a **locker** plugin to **generate** PEP 751 lockfiles, verify they are **in sync** with the configured dependency inputs, and **apply** them when syncing a `locked` environment. Built-in lockers are **`uv`** and **`pip`**, matching the [virtual environment installer](../how-to/environment/select-installer.md).

**Dependency lockers** are registered with `hatch_register_locker` (see [Registration](#registration) below).

## Registration

```python tab="hooks.py"
from hatchling.plugin import hookimpl

from .locker import MyLocker


@hookimpl
def hatch_register_locker():
    return MyLocker
```

Expose the module on the `hatch` entry point (see [Plugins — Discovery](about.md#discovery)) and list the distribution under [`tool.hatch.env.requires`](environment/reference.md#installation) when the plugin is not installed globally.

## Configuration

- Global default: [`tool.hatch.locker`](../config/environment/overview.md#locker) (string plugin name).
- Per environment: [`tool.hatch.envs.<name>.locker`](../config/environment/overview.md#locker) overrides the global value.
- If unset, Hatch picks `uv` when the environment uses the UV installer, otherwise `pip`.

## Built-in lockers

| `PLUGIN_NAME` | When selected | Notes |
| ------------- | ------------- | ----- |
| `uv` | Virtual env + UV installer | `uv pip compile` / `uv pip sync`; supports layered locks (extras, dependency-groups, `pyproject.toml`). |
| `pip` | Any supported environment | `pip lock`; flat dependency list only (no layered extras/groups in the pip locker). `apply_lock` is a no-op — use UV for `locked` installs from a pylock today. |
