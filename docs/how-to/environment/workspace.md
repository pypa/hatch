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

## Cross-member dependencies

Workspace members can depend on each other. When installed, pip or uv will resolve the dependency relationships:

```toml config-example title="packages/app/pyproject.toml"
[project]
name = "app"
dependencies = ["core", "utils"]
```

```toml config-example title="pyproject.toml"
[tool.hatch.envs.default]
workspace.members = [
  "packages/core",
  "packages/utils", 
  "packages/app"
]
```

All workspace members are installed as editable packages. Pip or uv handles resolving the dependencies between app, core, and utils during installation.
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

## Multi-service application example

Configuration for microservices development:

```toml config-example
[tool.hatch.envs.default]
workspace.members = ["shared"]
dependencies = ["pytest", "requests"]

[tool.hatch.envs.api]
workspace.members = [
  "shared",
  {path = "services/api", features = ["dev"]}
]
dependencies = ["fastapi", "uvicorn"]
scripts.dev = "uvicorn services.api.main:app --reload"

[tool.hatch.envs.worker]
workspace.members = [
  "shared", 
  {path = "services/worker", features = ["dev"]}
]
dependencies = ["celery", "redis"]
scripts.dev = "celery -A services.worker.tasks worker --loglevel=info"

[tool.hatch.envs.integration]
workspace.members = [
  "shared",
  "services/api",
  "services/worker",
  "services/frontend"
]
dependencies = ["pytest", "httpx", "docker"]
scripts.test = "pytest tests/integration {args}"
```

## Documentation generation example

Configuration for generating documentation across packages:

```toml config-example
[tool.hatch.envs.docs]
workspace.members = [
  {path = "packages/core", features = ["docs"]},
  {path = "packages/cli", features = ["docs"]},
  {path = "packages/plugins", features = ["docs"]}
]
dependencies = [
  "mkdocs",
  "mkdocs-material", 
  "mkdocstrings[python]"
]
scripts.serve = "mkdocs serve"
scripts.build = "mkdocs build"

[tool.hatch.envs.docs-api-only]
workspace.members = [
  {path = "packages/core", features = ["docs"]}
]
template = "docs"
scripts.serve = "mkdocs serve --config-file mkdocs-api.yml"
```

## Development workflow example

Configuration supporting different development workflows:

```toml config-example
[tool.hatch.envs.dev]
workspace.members = ["packages/*"]
workspace.parallel = true
dependencies = [
  "pytest",
  "black", 
  "ruff",
  "mypy",
  "pre-commit"
]
scripts.setup = "pre-commit install"
scripts.test = "pytest {args}"
scripts.lint = ["ruff check .", "black --check .", "mypy ."]
scripts.fmt = ["ruff check --fix .", "black ."]

[tool.hatch.envs.feature]
template = "dev"
workspace.members = [
  "packages/core",
  "packages/{env:FEATURE_PACKAGE}"
]
scripts.test = "pytest packages/{env:FEATURE_PACKAGE}/tests {args}"

[[tool.hatch.envs.release.matrix]]
package = ["core", "utils", "cli"]

[tool.hatch.envs.release]
detached = true
workspace.members = ["packages/{matrix:package}"]
dependencies = ["build", "twine"]
scripts.build = "python -m build packages/{matrix:package}"
scripts.publish = "twine upload packages/{matrix:package}/dist/*"
```