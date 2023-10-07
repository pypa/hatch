# Project templates

-----

You can control how new projects are created by the [new](../cli/reference.md#hatch-new) command using Hatch's [config file](hatch.md).

## Author

```toml tab="config.toml"
[template]
name = "..."
email = "..."
```

## Licenses

```toml tab="config.toml"
[template.licenses]
headers = true
default = [
  "MIT",
]
```

The list of licenses should be composed of [SPDX identifiers](https://spdx.org/licenses/). If multiple licenses are specified, then they will be placed in a [LICENSES](https://reuse.software/faq/#multi-licensing) directory.

## Options

### Tests

This adds a `tests` directory with environments for testing and linting.

```toml tab="config.toml"
[template.plugins.default]
tests = true
```

### CI

This adds a [GitHub Actions workflow](https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions#workflows) that runs tests on all platforms using modern versions of Python.

```toml tab="config.toml"
[template.plugins.default]
ci = false
```

### `src` layout

See [this blog post](https://blog.ionelmc.ro/2014/05/25/python-packaging/).

```toml tab="config.toml"
[template.plugins.default]
src-layout = true
```

## Feature flags

### Command line interface

The `--cli` flag adds a CLI backed by [Click](https://github.com/pallets/click) that can also be invoked with `python -m <PKG_NAME>`.
