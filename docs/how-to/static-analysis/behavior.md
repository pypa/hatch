# Customize static analysis behavior

-----

You can [fully alter](../../config/internal/static-analysis.md#customize-behavior) the static analysis performed by the [`check code`](../../cli/reference.md#hatch-check-code) and [`check fmt`](../../cli/reference.md#hatch-check-fmt) commands by modifying the reserved [environments](../../config/environment/overview.md) named `hatch-check-code` and `hatch-check-fmt`.

For example, you could define the following if you wanted to replace the default linting behavior with [flake8](https://github.com/PyCQA/flake8) and the default formatting with a mix of [Black](https://github.com/psf/black) and [isort](https://github.com/PyCQA/isort):

```toml config-example
[tool.hatch.envs.hatch-check-code]
dependencies = ["flake8"]

[tool.hatch.envs.hatch-check-code.scripts]
lint-check = "flake8 {args:.}"
lint-fix = "lint-check"

[tool.hatch.envs.hatch-check-fmt]
dependencies = ["black", "isort"]

[tool.hatch.envs.hatch-check-fmt.scripts]
format-check = [
  "black --check --diff {args:.}",
  "isort --check-only --diff {args:.}",
]
format-fix = [
  "isort {args:.}",
  "black {args:.}",
]
```

The `lint-*` scripts are used by `hatch check code` while the `format-*` scripts are used by `hatch check fmt`. The `*-fix` scripts run when `--fix` is passed, while the `*-check` scripts run by default. Based on this example, the following shows how the various scripts influence behavior:

| Command | Expanded scripts |
| --- | --- |
| `hatch check code` | <ul><li><code>flake8 .</code></li></ul> |
| `hatch check code --fix` | <ul><li><code>flake8 .</code></li></ul> |
| `hatch check code src tests` | <ul><li><code>flake8 src tests</code></li></ul> |
| `hatch check fmt` | <ul><li><code>black --check --diff .</code></li><li><code>isort --check-only --diff .</code></li></ul> |
| `hatch check fmt --fix` | <ul><li><code>isort .</code></li><li><code>black .</code></li></ul> |
| `hatch check fmt --fix src tests` | <ul><li><code>isort src tests</code></li><li><code>black src tests</code></li></ul> |

!!! note
    If you choose to use different tools for static analysis, be sure to update the required [dependencies](../../config/internal/static-analysis.md#dependencies).
