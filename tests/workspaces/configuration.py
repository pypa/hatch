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

    def test_workspace_inheritance_from_root(self, temp_dir, hatch):
        """Test that workspace members inherit environments from root."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        workspace_config = workspace_root / "pyproject.toml"
        workspace_config.write_text("""
[project]
name = "workspace-root"
version = "0.1.0"

[tool.hatch.envs.default]
workspace.members = ["packages/*"]

[tool.hatch.envs.shared]
dependencies = ["pytest", "black"]
scripts.test = "pytest"
""")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        member_dir = packages_dir / "member1"
        member_dir.mkdir()
        (member_dir / "pyproject.toml").write_text("""
[project]
name = "member1"
version = "0.1.0"

[tool.hatch.envs.default]
dependencies = ["requests"]
""")

        with workspace_root.as_cwd():
            result = hatch("env", "show", "shared")
            assert result.exit_code == 0

        with member_dir.as_cwd():
            result = hatch("env", "show", "shared")
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
