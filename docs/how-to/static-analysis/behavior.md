# Customize static analysis behavior

-----

You can [fully alter](../../config/internal/static-analysis.md#customize-behavior) the static analysis performed by the [`fmt`](../../cli/reference.md#hatch-fmt) command by modifying the reserved [environment](../../config/environment/overview.md) named `hatch-static-analysis`. For example, you could define the following if you wanted to replace the default behavior with a mix of [Black](https://github.com/psf/black), [isort](https://github.com/PyCQA/isort) and basic [flake8](https://github.com/PyCQA/flake8):

```toml config-example
[tool.hatch.envs.hatch-static-analysis]
dependencies = ["black", "flake8", "isort"]

[tool.hatch.envs.hatch-static-analysis.scripts]
format-check = [
  "black --check --diff {args:.}",
  "isort --check-only --diff {args:.}",
]
format-fix = [
  "isort {args:.}",
  "black {args:.}",
]
lint-check = "flake8 {args:.}"
lint-fix = "lint-check"
```

The `format-*` scripts correspond to the `--formatter`/`-f` flag while the `lint-*` scripts correspond to the `--linter`/`-l` flag. The `*-fix` scripts run by default while the `*-check` scripts correspond to the `--check` flag. Based on this example, the following shows how the various scripts influence behavior:

| Command | Expanded scripts |
| --- | --- |
| `hatch fmt` | <ul><li><code>flake8 .</code></li><li><code>isort .</code></li><li><code>black .</code></li></ul> |
| `hatch fmt src tests` | <ul><li><code>flake8 src tests</code></li><li><code>isort src tests</code></li><li><code>black src tests</code></li></ul> |
| `hatch fmt -f` | <ul><li><code>isort .</code></li><li><code>black .</code></li></ul> |
| `hatch fmt -l` | <ul><li><code>flake8 .</code></li></ul> |
| `hatch fmt --check` | <ul><li><code>flake8 .</code></li><li><code>black --check --diff .</code></li><li><code>isort --check-only --diff .</code></li></ul> |
| `hatch fmt --check -f` | <ul><li><code>black --check --diff .</code></li><li><code>isort --check-only --diff .</code></li></ul> |
| `hatch fmt --check -l` | <ul><li><code>flake8 .</code></li></ul> |
