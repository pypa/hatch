# Static analysis configuration

-----

Static analysis performed by the [`fmt`](../../cli/reference.md#hatch-fmt) command is ([by default](#customize-behavior)) backed entirely by [Ruff](https://github.com/astral-sh/ruff).

Hatch provides [default settings](#default-settings) that user configuration can [extend](#extending-config).

## Extending config

When defining your configuration, be sure to use options that are prefixed by `extend-` such as [`extend-select`](https://docs.astral.sh/ruff/settings/#extend-select), for example:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.ruff.format]
    preview = true
    quote-style = "single"

    [tool.ruff.lint]
    preview = true
    extend-select = ["C901"]

    [tool.ruff.lint.extend-per-file-ignores]
    "docs/.hooks/*" = ["INP001", "T201"]

    [tool.ruff.lint.isort]
    known-first-party = ["foo", "bar"]
    ```

=== ":octicons-file-code-16: ruff.toml"

    ```toml
    [format]
    preview = true
    quote-style = "single"

    [lint]
    preview = true
    extend-select = ["C901"]

    [lint.extend-per-file-ignores]
    "docs/.hooks/*" = ["INP001", "T201"]

    [lint.isort]
    known-first-party = ["foo", "bar"]
    ```

!!! note
    When not [persisting config](#persistent-config), there is no need to explicitly [extend](https://docs.astral.sh/ruff/settings/#extend) the defaults as Hatch automatically handles that.

## Persistent config

If you want to store the default configuration in the project, set an explicit path like so:

```toml config-example
[tool.hatch.envs.hatch-static-analysis]
config-path = "ruff_defaults.toml"
```

Then instruct Ruff to consider your configuration as an extension of the default file:

=== ":octicons-file-code-16: pyproject.toml"

    ```toml
    [tool.ruff]
    extend = "ruff_defaults.toml"
    ```

=== ":octicons-file-code-16: ruff.toml"

    ```toml
    extend = "ruff_defaults.toml"
    ```

Anytime you wish to update the defaults (such as when upgrading Hatch), you must run the [`fmt`](../../cli/reference.md#hatch-fmt) command once with the `--sync` flag e.g.:

```
hatch fmt --check --sync
```

!!! tip
    This is the recommended approach since it allows other tools like IDEs to use the default configuration.

### No config

If you don't want Hatch to use any of its default configuration and rely entirely on yours, set the path to anything and then simply don't `extend` in your Ruff config:

```toml config-example
[tool.hatch.envs.hatch-static-analysis]
config-path = "none"
```

## Customize behavior

You can fully alter the behavior of the environment used by the [`fmt`](../../cli/reference.md#hatch-fmt) command. See the [how-to](../../how-to/static-analysis/behavior.md) for a detailed example.

### Dependencies

Pin the particular version of Ruff by explicitly defining the environment [dependencies](../environment/overview.md#dependencies):

```toml config-example
[tool.hatch.envs.hatch-static-analysis]
dependencies = ["ruff==X.Y.Z"]
```

### Scripts

If you want to change the default commands that are executed, you can override the [scripts](../environment/overview.md#scripts). The following four scripts must be defined:

```toml config-example
[tool.hatch.envs.hatch-static-analysis.scripts]
format-check = "..."
format-fix = "..."
lint-check = "..."
lint-fix = "..."
```

The `format-*` scripts correspond to the `--formatter`/`-f` flag while the `lint-*` scripts correspond to the `--linter`/`-l` flag. The `*-fix` scripts run by default while the `*-check` scripts correspond to the `--check` flag.

!!! note "Reminder"
    If you choose to use different tools for static analysis, be sure to update the required [dependencies](#dependencies).

### Installer

By default, [UV is enabled](../../how-to/environment/select-installer.md). You may disable that behavior as follows:

```toml config-example
[tool.hatch.envs.hatch-static-analysis]
installer = "pip"
```

## Default settings

### Non-rule settings

- [Line length](https://docs.astral.sh/ruff/settings/#line-length) set to 120
- [Docstring formatting](https://docs.astral.sh/ruff/formatter/#docstring-formatting) enabled with [line length](https://docs.astral.sh/ruff/settings/#format_docstring-code-line-length) set to 80
- Only absolute imports [are allowed](https://docs.astral.sh/ruff/settings/#lint_flake8-tidy-imports_ban-relative-imports), [except for tests](#per-file-ignored-rules)
- The normalized [project name](../metadata.md#name) is a [known first party](https://docs.astral.sh/ruff/settings/#lint_isort_known-first-party) import

### Per-file ignored rules

<HATCH_RUFF_PER_FILE_IGNORED_RULES>

### Selected rules

The following rules are based on version <HATCH_RUFF_VERSION> of Ruff. Rules with a ^P^ are only selected when [preview](https://docs.astral.sh/ruff/preview/) mode is enabled.

There are <HATCH_RUFF_STABLE_RULES_COUNT> selected stable rules and <HATCH_RUFF_PREVIEW_RULES_COUNT> selected preview rules.

<HATCH_RUFF_SELECTED_RULES>

#### Unselected

There are <HATCH_RUFF_UNSELECTED_RULES_COUNT> unselected rules.

<HATCH_RUFF_UNSELECTED_RULES>
