class TestWorkspaceConfiguration:
    def test_workspace_members_editable_install(self, temp_dir, hatch):
        """Test that workspace members are installed as editable packages."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "workspace-root"
version = "0.1.0"

[tool.hatch.envs.default]
type = "virtual"
workspace.members = ["packages/*"]
""")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        member1_dir = packages_dir / "member1"
        member1_dir.mkdir()
        (member1_dir / "pyproject.toml").write_text("""
[project]
name = "member1"
version = "0.1.0"
dependencies = ["requests"]
""")

        member2_dir = packages_dir / "member2"
        member2_dir.mkdir()
        (member2_dir / "pyproject.toml").write_text("""
[project]
name = "member2"
version = "0.1.0"
dependencies = ["click"]
""")

        with workspace_root.as_cwd():
            result = hatch("env", "create")
            assert result.exit_code == 0

            result = hatch("env", "show", "--json")
            assert result.exit_code == 0

    def test_workspace_exclude_patterns(self, temp_dir, hatch):
        """Test that exclude patterns filter out workspace members."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "workspace-root"
version = "0.1.0"

[tool.hatch.envs.default]
workspace.members = ["packages/*"]
workspace.exclude = ["packages/excluded*"]
""")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        included_dir = packages_dir / "included"
        included_dir.mkdir()
        (included_dir / "pyproject.toml").write_text("""
[project]
name = "included"
version = "0.1.0"
""")

        excluded_dir = packages_dir / "excluded-pkg"
        excluded_dir.mkdir()
        (excluded_dir / "pyproject.toml").write_text("""
[project]
name = "excluded-pkg"
version = "0.1.0"
""")

        with workspace_root.as_cwd():
            result = hatch("env", "create")
            assert result.exit_code == 0

    def test_workspace_parallel_dependency_resolution(self, temp_dir, hatch):
        """Test parallel dependency resolution for workspace members."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "workspace-root"
version = "0.1.0"

[tool.hatch.envs.default]
workspace.members = ["packages/*"]
workspace.parallel = true
""")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        for i in range(3):
            member_dir = packages_dir / f"member{i}"
            member_dir.mkdir()
            (member_dir / "pyproject.toml").write_text(f"""
[project]
name = "member{i}"
version = "0.1.{i}"
dependencies = ["requests"]
""")

        with workspace_root.as_cwd():
            result = hatch("env", "create")
            assert result.exit_code == 0

    def test_workspace_member_features(self, temp_dir, hatch):
        """Test workspace members with specific features."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "workspace-root"
version = "0.1.0"

[tool.hatch.envs.default]
workspace.members = [
    {path = "packages/member1", features = ["dev", "test"]}
]
""")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        member1_dir = packages_dir / "member1"
        member1_dir.mkdir()
        (member1_dir / "pyproject.toml").write_text("""
[project]
name = "member1"
dependencies = ["requests"]
version = "0.1.0"
[project.optional-dependencies]
dev = ["black", "ruff"]
test = ["pytest"]
""")

        with workspace_root.as_cwd():
            result = hatch("env", "create")
            assert result.exit_code == 0

    def test_workspace_no_members_fallback(self, temp_dir, hatch):
        """Test fallback when no workspace members are defined."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "workspace-root"
version = "0.1.0"

[tool.hatch.envs.default]
dependencies = ["requests"]
""")

        with workspace_root.as_cwd():
            result = hatch("env", "create")
            assert result.exit_code == 0

            result = hatch("env", "show", "--json")
            assert result.exit_code == 0

    def test_workspace_cross_member_dependencies(self, temp_dir, hatch):
        """Test workspace members depending on each other."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "workspace-root"
version = "0.1.0"

[tool.hatch.envs.default]
workspace.members = ["packages/*"]
""")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        base_dir = packages_dir / "base"
        base_dir.mkdir()
        (base_dir / "pyproject.toml").write_text("""
[project]
name = "base"
version = "0.1.0"
dependencies = ["requests"]
""")

        app_dir = packages_dir / "app"
        app_dir.mkdir()
        (app_dir / "pyproject.toml").write_text("""
[project]
name = "app"
version = "0.1.0"
dependencies = ["base", "click"]
""")

        with workspace_root.as_cwd():
            result = hatch("env", "create")
            assert result.exit_code == 0

            result = hatch("dep", "show", "table")
            assert result.exit_code == 0

    def test_workspace_build_all_members(self, temp_dir, hatch):
        """Test building all workspace members."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_pkg = workspace_root / "workspace_root"
        workspace_pkg.mkdir()
        (workspace_pkg / "__init__.py").write_text('__version__ = "0.1.0"')

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "workspace-root"
version = "0.1.0"

[tool.hatch.envs.default]
workspace.members = ["packages/*"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["workspace_root"]
""")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        for i in range(2):
            member_dir = packages_dir / f"member{i}"
            member_dir.mkdir()
            (member_dir / "pyproject.toml").write_text(f"""
[project]
name = "member{i}"
version = "0.1.{i}"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["member{i}"]
""")

            src_dir = member_dir / f"member{i}"
            src_dir.mkdir()
            (src_dir / "__init__.py").write_text(f'__version__ = "0.1.{i}"')

        with workspace_root.as_cwd():
            result = hatch("build")
            assert result.exit_code == 0

    def test_environment_specific_workspace_slices(self, temp_dir, hatch):
        """Test different workspace slices per environment."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "workspace-root"
version = "0.1.0"

[tool.hatch.envs.unit-tests]
workspace.members = ["packages/core", "packages/utils"]
scripts.test = "pytest tests/unit"

[tool.hatch.envs.integration-tests]
workspace.members = ["packages/*"]
scripts.test = "pytest tests/integration"
""")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        for pkg in ["core", "utils", "extras"]:
            pkg_dir = packages_dir / pkg
            pkg_dir.mkdir()
            (pkg_dir / "pyproject.toml").write_text(f"""
[project]
name = "{pkg}"
version = "0.1.0"
""")

        with workspace_root.as_cwd():
            result = hatch("env", "create", "unit-tests")
            assert result.exit_code == 0

            result = hatch("env", "create", "integration-tests")
            assert result.exit_code == 0

    def test_workspace_test_matrices(self, temp_dir, hatch):
        """Test workspace configuration with test matrices."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "workspace-root"
version = "0.1.0"

[[tool.hatch.envs.test.matrix]]
python = ["3.9", "3.10"]

[tool.hatch.envs.test]
workspace.members = ["packages/*"]
dependencies = ["pytest", "coverage"]
scripts.test = "pytest {args}"

[[tool.hatch.envs.test-core.matrix]]
python = ["3.9", "3.10"]

[tool.hatch.envs.test-core]
workspace.members = ["packages/core"]
dependencies = ["pytest", "coverage"]
scripts.test = "pytest packages/core/tests {args}"
""")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        for pkg in ["core", "utils"]:
            pkg_dir = packages_dir / pkg
            pkg_dir.mkdir()
            (pkg_dir / "pyproject.toml").write_text(f"""
[project]
name = "{pkg}"
version = "0.1.0"
""")

        with workspace_root.as_cwd():
            result = hatch("env", "show", "test")
            assert result.exit_code == 0

            result = hatch("env", "show", "test-core")
            assert result.exit_code == 0

    def test_workspace_library_with_plugins(self, temp_dir, hatch):
        """Test library with plugins workspace configuration."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
    [project]
    name = "library-root"
    version = "0.1.0"

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [tool.hatch.build.targets.wheel]
    packages = []

    [tool.hatch.envs.default]
    skip-install = true
    workspace.members = ["core"]
    dependencies = ["pytest"]

    [tool.hatch.envs.full]
    skip-install = true
    workspace.members = [
      "core",
      "plugins/database",
      "plugins/cache",
      "plugins/auth"
    ]
    dependencies = ["pytest", "pytest-asyncio"]

    [tool.hatch.envs.database-only]
    skip-install = true
    workspace.members = [
      "core",
      {path = "plugins/database", features = ["postgresql", "mysql"]}
    ]
    """)

        # Create core package with source
        core_dir = workspace_root / "core"
        core_dir.mkdir()
        (core_dir / "pyproject.toml").write_text("""
    [project]
    name = "core"
    version = "0.1.0"

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [tool.hatch.build.targets.wheel]
    packages = ["core"]
    """)
        core_src = core_dir / "core"
        core_src.mkdir()
        (core_src / "__init__.py").write_text("")

        # Create plugins with source
        plugins_dir = workspace_root / "plugins"
        plugins_dir.mkdir()

        for plugin in ["database", "cache", "auth"]:
            plugin_dir = plugins_dir / plugin
            plugin_dir.mkdir()
            (plugin_dir / "pyproject.toml").write_text(f"""
    [project]
    name = "{plugin}"
    version = "0.1.0"
    dependencies = ["core"]

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [tool.hatch.build.targets.wheel]
    packages = ["{plugin}"]

    [project.optional-dependencies]
    postgresql = ["requests"]
    mysql = ["click"]
    """)
            plugin_src = plugin_dir / plugin
            plugin_src.mkdir()
            (plugin_src / "__init__.py").write_text("")

        with workspace_root.as_cwd():
            result = hatch("env", "create", "full")
            assert result.exit_code == 0

            result = hatch("env", "create", "database-only")
            assert result.exit_code == 0

    def test_workspace_multi_service_application(self, temp_dir, hatch):
        """Test multi-service application workspace configuration."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
    [project]
    name = "microservices-root"
    version = "0.1.0"

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [tool.hatch.build.targets.wheel]
    packages = []

    [tool.hatch.envs.default]
    skip-install = true
    workspace.members = ["shared"]
    dependencies = ["pytest", "requests"]

    [tool.hatch.envs.api]
    skip-install = true
    workspace.members = [
      "shared",
      {path = "services/api", features = ["dev"]}
    ]
    dependencies = ["fastapi", "uvicorn"]
    scripts.dev = "uvicorn services.api.main:app --reload"

    [tool.hatch.envs.worker]
    skip-install = true
    workspace.members = [
      "shared",
      {path = "services/worker", features = ["dev"]}
    ]
    dependencies = ["celery", "redis"]
    scripts.dev = "celery -A services.worker.tasks worker --loglevel=info"

    [tool.hatch.envs.integration]
    skip-install = true
    workspace.members = [
      "shared",
      "services/api",
      "services/worker",
      "services/frontend"
    ]
    dependencies = ["pytest", "httpx", "docker"]
    scripts.test = "pytest tests/integration {args}"
    """)

        # Create shared package with source
        shared_dir = workspace_root / "shared"
        shared_dir.mkdir()
        (shared_dir / "pyproject.toml").write_text("""
    [project]
    name = "shared"
    version = "0.1.0"

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [tool.hatch.build.targets.wheel]
    packages = ["shared"]
    """)
        shared_src = shared_dir / "shared"
        shared_src.mkdir()
        (shared_src / "__init__.py").write_text("")

        # Create services with source
        services_dir = workspace_root / "services"
        services_dir.mkdir()

        for service in ["api", "worker", "frontend"]:
            service_dir = services_dir / service
            service_dir.mkdir()
            (service_dir / "pyproject.toml").write_text(f"""
    [project]
    name = "{service}"
    version = "0.1.0"
    dependencies = ["shared"]

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [tool.hatch.build.targets.wheel]
    packages = ["{service}"]

    [project.optional-dependencies]
    dev = ["black", "ruff"]
    """)
            service_src = service_dir / service
            service_src.mkdir()
            (service_src / "__init__.py").write_text("")

        with workspace_root.as_cwd():
            result = hatch("env", "create", "api")
            assert result.exit_code == 0

            result = hatch("env", "create", "worker")
            assert result.exit_code == 0

            result = hatch("env", "create", "integration")
            assert result.exit_code == 0

    def test_workspace_documentation_generation(self, temp_dir, hatch):
        """Test documentation generation workspace configuration."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "docs-root"
version = "0.1.0"

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
""")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        for pkg in ["core", "cli", "plugins"]:
            pkg_dir = packages_dir / pkg
            pkg_dir.mkdir()
            (pkg_dir / "pyproject.toml").write_text(f"""
[project]
name = "{pkg}"
version = "0.1.0"
[project.optional-dependencies]
docs = ["sphinx", "sphinx-rtd-theme"]
""")

        with workspace_root.as_cwd():
            result = hatch("env", "create", "docs")
            assert result.exit_code == 0

            result = hatch("env", "create", "docs-api-only")
            assert result.exit_code == 0

    def test_workspace_development_workflow(self, temp_dir, hatch, monkeypatch):
        """Test development workflow workspace configuration."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
    [project]
    name = "dev-workflow-root"
    version = "0.1.0"

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [tool.hatch.build.targets.wheel]
    packages = []

    [tool.hatch.envs.dev]
    skip-install = true
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
    skip-install = true
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
    skip-install = true
    workspace.members = ["packages/{matrix:package}"]
    dependencies = ["build", "twine"]
    scripts.build = "python -m build packages/{matrix:package}"
    scripts.publish = "twine upload packages/{matrix:package}/dist/*"
    """)

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        for pkg in ["core", "utils", "cli"]:
            pkg_dir = packages_dir / pkg
            pkg_dir.mkdir()
            (pkg_dir / "pyproject.toml").write_text(f"""
    [project]
    name = "{pkg}"
    version = "0.1.0"

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [tool.hatch.build.targets.wheel]
    packages = ["{pkg}"]
    """)
            pkg_src = pkg_dir / pkg
            pkg_src.mkdir()
            (pkg_src / "__init__.py").write_text("")

        with workspace_root.as_cwd():
            result = hatch("env", "create", "dev")
            assert result.exit_code == 0

            # Test feature environment with environment variable
            monkeypatch.setenv("FEATURE_PACKAGE", "utils")
            result = hatch("env", "create", "feature")
            assert result.exit_code == 0

            result = hatch("env", "create", "release")
            assert result.exit_code == 0

    def test_workspace_overrides_matrix_conditional_members(self, temp_dir, hatch):
        """Test workspace members added conditionally via matrix overrides."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
    [project]
    name = "workspace-root"
    version = "0.1.0"

    [[tool.hatch.envs.test.matrix]]
    python = ["3.9", "3.11"]

    [tool.hatch.envs.test]
    workspace.members = ["packages/core"]

    [tool.hatch.envs.test.overrides]
    matrix.python.workspace.members = [
        { value = "packages/py311-only", if = ["3.11"] }
    ]
    """)

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        # Core package (always included)
        core_dir = packages_dir / "core"
        core_dir.mkdir()
        (core_dir / "pyproject.toml").write_text("""
    [project]
    name = "core"
    version = "0.1.0"
    """)

        # Python 3.11+ only package
        py311_dir = packages_dir / "py311-only"
        py311_dir.mkdir()
        (py311_dir / "pyproject.toml").write_text("""
    [project]
    name = "py311-only"
    version = "0.1.0"
    """)

        with workspace_root.as_cwd():
            # Both environments should be created
            result = hatch("env", "create", "test")
            assert result.exit_code == 0

    def test_workspace_overrides_platform_conditional_members(self, temp_dir, hatch):
        """Test workspace members added conditionally via platform overrides."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
    [project]
    name = "workspace-root"
    version = "0.1.0"

    [tool.hatch.envs.default]
    workspace.members = ["packages/core"]

    [tool.hatch.envs.default.overrides]
    platform.linux.workspace.members = ["packages/linux-specific"]
    platform.windows.workspace.members = ["packages/windows-specific"]
    """)

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        for pkg in ["core", "linux-specific", "windows-specific"]:
            pkg_dir = packages_dir / pkg
            pkg_dir.mkdir()
            (pkg_dir / "pyproject.toml").write_text(f"""
    [project]
    name = "{pkg}"
    version = "0.1.0"
    """)

        with workspace_root.as_cwd():
            result = hatch("env", "create")
            assert result.exit_code == 0

    def test_workspace_overrides_combined_conditions(self, temp_dir, hatch):
        """Test workspace members with combined matrix and platform conditions."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
    [project]
    name = "workspace-root"
    version = "0.1.0"

    [[tool.hatch.envs.test.matrix]]
    python = ["3.9", "3.11"]

    [tool.hatch.envs.test]
    workspace.members = ["packages/core"]

    [tool.hatch.envs.test.overrides]
    matrix.python.workspace.members = [
        { value = "packages/linux-py311", if = ["3.11"], platform = ["linux"] }
    ]
    """)

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        for pkg in ["core", "linux-py311"]:
            pkg_dir = packages_dir / pkg
            pkg_dir.mkdir()
            (pkg_dir / "pyproject.toml").write_text(f"""
    [project]
    name = "{pkg}"
    version = "0.1.0"
    """)

        with workspace_root.as_cwd():
            result = hatch("env", "create", "test")
            assert result.exit_code == 0
