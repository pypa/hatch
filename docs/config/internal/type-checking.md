# Type checking configuration

-----

Type checking performed by the [`check types`](../../cli/reference.md#hatch-check-types) command is ([by default](#customize-behavior)) backed by [Pyrefly](https://github.com/facebook/pyrefly).

## Configuration

When no user configuration is detected, Hatch auto-generates a `pyrefly.toml` config file that:

- Detects source directories (src layout, workspace members, tests)
- Sets appropriate search paths for import resolution
- Uses the `legacy` preset for relaxed type checking suitable for existing codebases
- Ignores platform-conditional dependencies that aren't installed locally

### User configuration

Hatch respects existing Pyrefly configuration. If any of the following exist, the auto-generated config will not be used:

- A `pyrefly.toml` file in the project root
- A `[tool.pyrefly]` section in `pyproject.toml`

### Persistent config

If you want to store the default configuration in the project, set an explicit path:

```toml config-example
[tool.hatch.envs.hatch-check-types]
config-path = "pyrefly.toml"
```

## Customize behavior

You can fully alter the behavior of the environment used by the [`check types`](../../cli/reference.md#hatch-check-types) command by modifying the reserved [environment](../../config/environment/overview.md) named `hatch-check-types`.

### Dependencies

The environment includes Pyrefly and all test dependencies (inherited from the `hatch-test` environment) to ensure type checking has access to all imports. Pin the particular version of Pyrefly by explicitly defining the environment [dependencies](../environment/overview.md#dependencies):

```toml config-example
[tool.hatch.envs.hatch-check-types]
dependencies = ["pyrefly==X.Y.Z"]
```

### Scripts

If you want to change the default commands that are executed, you can override the [scripts](../environment/overview.md#scripts):

```toml config-example
[tool.hatch.envs.hatch-check-types.scripts]
check = "..."
check-summarize = "..."
coverage = "..."
```

The `check` script runs by default. The `check-summarize` script runs when the `--summarize` flag is passed. The `coverage` script runs when the `--cover` flag is passed.

### Installer

By default, [UV is enabled](../../how-to/environment/select-installer.md). You may disable that behavior as follows:

```toml config-example
[tool.hatch.envs.hatch-check-types]
installer = "pip"
```
