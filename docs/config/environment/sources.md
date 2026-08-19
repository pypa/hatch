# Environment sources

-----

The `sources` table of an environment redirects dependencies to alternative origins at install time without changing your project's published metadata. This is useful during development when you want to consume a dependency from a local checkout, a Git branch, a private index, or another workspace member, while keeping the released wheel pointing at the version you ship.

A source is matched against your dependencies by name, after [PEP 503 normalization](https://peps.python.org/pep-0503/#normalized-names). Both [project dependencies](../metadata.md#dependencies) and [environment dependencies](overview.md#dependencies) are eligible for redirection.

```toml config-example
[project]
dependencies = ["foo"]

[tool.hatch.envs.default.sources]
foo = "./packages/foo"
```

The top-level `[tool.hatch.sources]` table is an alias for the `default` environment, so the following is equivalent:

```toml config-example
[tool.hatch.sources]
foo = "./packages/foo"
```

!!! note
    Sources only affect installs performed by Hatch when it manages an environment. They do not influence the metadata of wheels you build with `hatch build`.

## Inheritance

Sources follow the usual [inheritance](overview.md#inheritance) rules, merging entry by entry so that an environment can redirect a single dependency differently while every other entry it inherits stays in place:

```toml config-example
[tool.hatch.sources]
foo = "./packages/foo"
bar = "./packages/bar"

[tool.hatch.envs.test-upstream.sources]
foo = { git = "https://github.com/example/foo", branch = "main" }
```

Here every environment installs both `foo` and `bar` from the local checkouts, except `test-upstream`, which keeps the local `bar` but tracks the upstream development branch of `foo`.

An environment that does not inherit from `default`, such as a [detached](overview.md#detached-environments) one, receives no sources.

## Path

Use a relative or absolute path to a wheel, source distribution, or project directory:

```toml config-example
[tool.hatch.sources]
foo = "./packages/foo"
```

The shorthand above is equivalent to the full form:

```toml config-example
[tool.hatch.sources]
foo = { path = "./packages/foo", editable = true }
```

`editable` defaults to `true` to match Hatch's existing handling of local installs. Set `editable = false` for a non-editable install. If the package lives below the path root, set `subdirectory`:

```toml config-example
[tool.hatch.sources]
foo = { path = "./monorepo", subdirectory = "packages/foo" }
```

For editable installs the subdirectory is resolved into the path itself (equivalent to `path = "./monorepo/packages/foo"`), since installers expect a bare project directory. For non-editable installs the subdirectory is passed as a URL fragment, which also supports archives.

## Git

Pull from a Git repository:

```toml config-example
[tool.hatch.sources]
foo = { git = "https://github.com/example/foo" }
```

Pin to a specific revision with one of `rev`, `tag`, or `branch` (mutually exclusive):

```toml config-example
[tool.hatch.sources]
foo = { git = "https://github.com/example/foo", rev = "abc1234" }
bar = { git = "https://github.com/example/bar", tag = "v1.0" }
baz = { git = "https://github.com/example/baz", branch = "main" }
```

Use `subdirectory` when the Python package is not at the repository root.

## URL

Install a wheel or source archive from a URL:

```toml config-example
[tool.hatch.sources]
foo = { url = "https://files.example.com/foo-1.0.tar.gz" }
```

`subdirectory` is also supported for archives where the package is not at the root.

## Index

Resolve the dependency from a specific package index:

```toml config-example
[tool.hatch.sources]
foo = { index = "https://pypi.example.com/simple" }
```

The index URL is passed to the installer as `--extra-index-url`, so the default index (PyPI) remains the primary source. Multiple index sources are deduplicated and order-preserving.

## Workspace

Resolve the dependency from a [workspace](../../how-to/environment/workspace.md) member:

```toml config-example
[tool.hatch.sources]
my-pkg = { workspace = true }
```

The actual install path is determined by the matching member in `tool.hatch.envs.<ENV_NAME>.workspace.members`. This lets you declare workspace membership in one place and reference it from many environments.

## Precedence

A dependency that already uses a [PEP 508 direct reference](../dependency.md#direct-references) is left untouched — the explicit URL on the dependency wins over a configured source.

## Disabling sources

Setting the `HATCH_NO_SOURCES` environment variable to any non-empty value disables all sources. This is useful in CI to verify that your published metadata resolves on its own, without local redirections:

```
HATCH_NO_SOURCES=1 hatch env create
```

## Inspecting sources

The [`dep show sources`](../../cli/reference.md#hatch-dep-show) command displays each configured source, its target, and the dependencies of the active environment that it redirects. Sources that match no dependencies are reported with a warning, which helps catch typos in source names since unmatched sources are otherwise silently ignored.

## Installer translation

Sources produce installer-agnostic instructions that Hatch renders into the right flags for the configured installer:

| Source | Per-dependency form | Global flags |
| --- | --- | --- |
| `path` (editable) | `--editable <resolved>` | none |
| `path` (non-editable) | `name @ file://<resolved>` | none |
| `git` | `name @ git+<url>[@<ref>]` | none |
| `url` | `name @ <url>` | none |
| `index` | unchanged | `--extra-index-url <url>` |
| `workspace` | resolved through `workspace.members` | none |

Both [`installer = "pip"`](overview.md#dependencies) and `installer = "uv"` accept the same flag forms, so the same source configuration works for either. When an environment is [`locked`](overview.md#locked), sources also apply during lock resolution: rewritten requirements flow into the lock inputs and index sources are passed to the resolver as `--extra-index-url`.

!!! note
    Sources do not apply to [build requirements](../build.md#build-system) (`build-system.requires` or build target dependencies). Build environments always resolve from declared metadata so that builds remain reproducible.
