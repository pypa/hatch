---
date: 2026-08-11
authors: [cjames23]
description: >-
  Hatch v1.18.0 brings dependency sources, workspace-wide builds, and a long list of fixes.
categories:
  - Release
---

# Hatch v1.18.0

Hatch [v1.18.0](https://github.com/pypa/hatch/releases/tag/hatch-v1.18.0) introduces dependency sources for redirecting packages at install time, a `--all` flag for building every workspace member at once, and a healthy batch of bug fixes.

<!-- more -->

## Dependency sources

The new [`sources`](../../config/environment/sources.md) table redirects a dependency to somewhere other than the index it would normally come from — a local checkout, a Git branch, a URL, a private index, or another workspace member — **without touching the metadata you publish**.

This is the workflow it is built for: you are developing against an unreleased fix in a library you depend on, and you want your environment to use your local clone while the wheel you ship keeps pointing at the released version.

```toml config-example
[project]
dependencies = ["foo"]

[tool.hatch.sources]
foo = "./packages/foo"
```

The top-level `[tool.hatch.sources]` table is an alias for the `default` environment, so the example above is shorthand for `[tool.hatch.envs.default.sources]`.

Sources are matched to your dependencies by name after [PEP 503](https://peps.python.org/pep-0503/#normalized-names) normalization, and both project dependencies and environment dependencies are eligible.

### Every kind of origin

```toml config-example
[tool.hatch.sources]
# A local project directory, editable by default
core = "./packages/core"
# A non-editable install from a subdirectory
utils = { path = "./monorepo", subdirectory = "packages/utils", editable = false }
# A Git branch, tag, or revision
client = { git = "https://github.com/example/client", branch = "main" }
# An archive
legacy = { url = "https://files.example.com/legacy-1.0.tar.gz" }
# A private index, passed to the installer as --extra-index-url
internal = { index = "https://pypi.example.com/simple" }
# A workspace member, resolved through workspace.members
my-pkg = { workspace = true }
```

The `workspace = true` form is worth calling out: it lets you declare membership once in `workspace.members` and reference it from as many environments as you like, rather than repeating paths.

### Inheritance

Sources merge entry by entry, so an environment can override a single redirection while everything else it inherits stays put:

```toml config-example
[tool.hatch.sources]
foo = "./packages/foo"
bar = "./packages/bar"

[tool.hatch.envs.test-upstream.sources]
foo = { git = "https://github.com/example/foo", branch = "main" }
```

Every environment here installs both packages from local checkouts, except `test-upstream`, which keeps the local `bar` but tracks upstream `foo`.

### Checking your work

Redirections that quietly do nothing are the failure mode worth guarding against, so [`hatch dep show sources`](../../cli/reference.md#hatch-dep-show) reports what each source targets and which dependencies of the active environment it actually redirects. A source matching no dependency is reported with a warning — which is usually how you find out you typed `httpx2` where you meant `httpx`.

To prove your published metadata still resolves on its own, set `HATCH_NO_SOURCES` to disable every redirection:

```
HATCH_NO_SOURCES=1 hatch env create
```

That is a good thing to put in CI.

A few deliberate boundaries: a dependency that already uses a [direct reference](../../config/dependency.md#direct-references) wins over a configured source, sources never apply to build requirements so that builds stay reproducible, and they do not influence the metadata of wheels produced by `hatch build`.

## Building every workspace member

[Workspaces](../../how-to/environment/workspace.md) arrived in v1.16.0, but releasing one still meant walking the members yourself. The [`build`](../../cli/reference.md#hatch-build) command now takes `--all`/`-a`:

```
hatch build --all
```

This builds an sdist and a wheel for the workspace root and for every member of the selected environment, consolidating the artifacts in the root's `dist` directory — ready to hand straight to `twine upload dist/*`. Pass a location to put them elsewhere:

```
hatch build --all out/artifacts
```

The root is built first and does not need to list itself as a member. If your top-level `pyproject.toml` has no `project` table and exists purely to hold workspace configuration, the root is skipped and only the members are built.

## Fixes

This release carries a larger-than-usual batch of fixes.

**`hatch run` responds to Ctrl-C again.** Commands run through `hatch run` had become uninterruptible: the parent process ignored `SIGINT`, and the child inherited that. Interrupting a long test run works as it should now.

**Free-threaded builds get free-threaded interpreters.** When Hatch itself runs on a free-threaded build and has to install a Python distribution, it was selecting a GIL-enabled one — silently changing the execution model of the environment it just created. It now selects the distribution matching the running interpreter, such as `3.14t`. The new selectors described below also reach environment configuration: `python = "3.14t"` was initially rejected there even though `hatch python install 3.14t` accepted it, and both paths now agree.

**Prereleases are never selected automatically.** With Python 3.15 distributions now available (currently 3.15.0rc1), the fallback that picks the latest compatible version could have handed you a release candidate without asking. Automatic selection is restricted to stable releases; a prerelease still installs when you request one explicitly.

**Type checking works on Windows.** The Pyrefly configuration Hatch generates for `hatch check types` embedded absolute paths containing backslashes, which TOML read as escape sequences, producing an invalid config.

**Environment creation survives uninstalled metadata hooks.** Creating an environment crashed when the project configured a metadata hook that was not installed in the Hatch CLI's own environment.

**Coverage data no longer leaks between runs.** `hatch test --cover` now erases stale coverage data before running, so results reflect the run in front of you.

**No more hardcoded reliance on `pip`.** Internal dependency installation now goes through `uv`.

## Also in this release

- `tool.hatch.requires-hatch` — a version specifier set that commands reading your project's metadata enforce against the running version of Hatch, so a project that depends on newer behavior can say so. See [how to constrain Hatch](../../how-to/config/constrain-hatch.md).
- `hatch version` can now bump a version that is statically defined by `project.version`, rewriting `pyproject.toml` in place instead of refusing. Pass `--force` to allow an explicit downgrade.
- Free-threaded distribution names such as `3.13t` and `3.14t` are first-class in the `python` commands and the environment `python` option, rather than requiring `HATCH_PYTHON_VARIANT_GIL`.
- Python 3.15 distributions are available to install, and the default CPython distributions have been upgraded to the 20260807 release.

### Support

If you or your organization finds value in what Hatch provides, consider sponsoring our maintainers [Ofek](https://github.com/sponsors/ofek) and [Cary](https://github.com/sponsors/cjames23) to assist with maintenance and more rapid development!
