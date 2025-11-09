# How to configure workspace environments

-----

Workspace environments allow you to manage multiple related packages within a single environment. This is useful for monorepos or projects with multiple interdependent packages.

## Basic workspace configuration

Define workspace members in your environment configuration using the `workspace.members` option:

```toml config-example
[tool.hatch.envs.default]
workspace.members = [
  "packages/core",
  "packages/utils",
  "packages/cli"
]
```

Workspace members are automatically installed as editable packages in the environment.

## Pattern matching

Use glob patterns to automatically discover workspace members:

```toml config-example
[tool.hatch.envs.default]
workspace.members = ["packages/*"]
```

## Excluding members

Exclude specific packages from workspace discovery:

```toml config-example
[tool.hatch.envs.default]
workspace.members = ["packages/*"]
workspace.exclude = ["packages/experimental*"]
```

## Member-specific features

Install specific optional dependencies for workspace members:

```toml config-example
[tool.hatch.envs.default]
workspace.members = [
  {path = "packages/core", features = ["dev"]},
  {path = "packages/utils", features = ["test", "docs"]},
  "packages/cli"
]
```

## Environment-specific workspaces

Different environments can include different workspace members:

```toml config-example
[tool.hatch.envs.unit-tests]
workspace.members = ["packages/core", "packages/utils"]
scripts.test = "pytest tests/unit"

[tool.hatch.envs.integration-tests]
workspace.members = ["packages/*"]
scripts.test = "pytest tests/integration"

[tool.hatch.envs.docs]
workspace.members = [
  {path = "packages/core", features = ["docs"]},
  {path = "packages/utils", features = ["docs"]}
]
```

## Test matrices with workspaces

Combine workspace configuration with test matrices:

```toml config-example
[[tool.hatch.envs.test.matrix]]
python = ["3.9", "3.10", "3.11", "3.12"]

[tool.hatch.envs.test]
workspace.members = ["packages/*"]
dependencies = ["pytest", "coverage"]
scripts.test = "pytest {args}"

[[tool.hatch.envs.test-core.matrix]]
python = ["3.9", "3.10", "3.11", "3.12"]

[tool.hatch.envs.test-core]
workspace.members = ["packages/core"]
dependencies = ["pytest", "coverage"]
scripts.test = "pytest packages/core/tests {args}"
```

## Performance optimization

Enable parallel dependency resolution for faster environment setup:

```toml config-example
[tool.hatch.envs.default]
workspace.members = ["packages/*"]
workspace.parallel = true
```

## Monorepo example

Complete configuration for a typical monorepo structure:

```toml config-example
# Root pyproject.toml
[project]
name = "my-monorepo"
version = "1.0.0"

[tool.hatch.envs.default]
workspace.members = ["packages/*"]
workspace.exclude = ["packages/experimental*"]
workspace.parallel = true
dependencies = ["pytest", "black", "ruff"]

[tool.hatch.envs.test]
workspace.members = [
  {path = "packages/core", features = ["test"]},
  {path = "packages/utils", features = ["test"]},
  "packages/cli"
]
dependencies = ["pytest", "coverage", "pytest-cov"]
scripts.test = "pytest --cov {args}"

[tool.hatch.envs.lint]
detached = true
workspace.members = ["packages/*"]
dependencies = ["ruff", "black", "mypy"]
scripts.check = ["ruff check .", "black --check .", "mypy ."]
scripts.fmt = ["ruff check --fix .", "black ."]

[[tool.hatch.envs.ci.matrix]]
python = ["3.9", "3.10", "3.11", "3.12"]

[tool.hatch.envs.ci]
template = "test"
workspace.parallel = false  # Disable for CI stability
```

## Library with plugins example

Configuration for a library with optional plugins:

```toml config-example
[tool.hatch.envs.default]
workspace.members = ["core"]
dependencies = ["pytest"]

[tool.hatch.envs.full]
workspace.members = [
  "core",
  "plugins/database",
  "plugins/cache",
  "plugins/auth"
]
dependencies = ["pytest", "pytest-asyncio"]

[tool.hatch.envs.database-only]
workspace.members = [
  "core",
  {path = "plugins/database", features = ["postgresql", "mysql"]}
]

[[tool.hatch.envs.plugin-test.matrix]]
plugin = ["database", "cache", "auth"]

[tool.hatch.envs.plugin-test]
workspace.members = [
  "core",
  "plugins/{matrix:plugin}"
]
scripts.test = "pytest plugins/{matrix:plugin}/tests {args}"
```
