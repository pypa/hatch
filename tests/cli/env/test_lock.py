import os

import pytest
import tomli_w

from hatch.config.constants import ConfigEnvVars
from hatch.project.core import Project
from hatch.utils.toml import load_toml_file


def _require_uv(uv_on_path: str | None) -> None:
    if not uv_on_path:
        pytest.skip("uv not found on PATH")


def _patch_pyproject_metadata(
    project_path,
    *,
    project_dependencies: list[str] | None = None,
    optional_dependencies: dict[str, list[str]] | None = None,
    dependency_groups: dict[str, list[str]] | None = None,
) -> None:
    """Merge packaging metadata into ``pyproject.toml`` for lock integration tests."""
    path = project_path / "pyproject.toml"
    data = load_toml_file(str(path))
    project = data.setdefault("project", {})
    if project_dependencies is not None:
        project["dependencies"] = project_dependencies
    if optional_dependencies is not None:
        project["optional-dependencies"] = optional_dependencies
    if dependency_groups is not None:
        data["dependency-groups"] = dependency_groups
    path.write_text(tomli_w.dumps(data), encoding="utf-8")


def test_undefined(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    with project_path.as_cwd():
        result = hatch("env", "lock", "test")

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Environment `test` is not defined by project config
        """
    )


def test_no_locked_envs(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    with project_path.as_cwd():
        result = hatch("env", "lock")

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        No environments are configured with `locked = true`
        """
    )


def test_non_locked_env_requires_export(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], **project.config.envs["default"]},
    )

    with project_path.as_cwd():
        result = hatch("env", "lock", "default")

    assert result.exit_code == 1
    assert "not configured with `locked = true`" in result.output
    assert "--export" in result.output


def test_no_dependencies(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    project = Project(project_path)
    helpers.update_project_environment(
        project, "default", {"skip-install": True, "locked": True, **project.config.envs["default"]}
    )

    with project_path.as_cwd():
        result = hatch("env", "lock", "default")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Environment `default` has no dependencies to lock
        """
    )


@pytest.mark.usefixtures("mock_locker")
def test_explicit_env(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], "locked": True, **project.config.envs["default"]},
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "default")

    assert result.exit_code == 0, result.output
    assert "Locking environment: default" in result.output
    assert f"Wrote lockfile: {project_path / 'pylock.toml'}" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_locked_env_no_arg(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], "locked": True, **project.config.envs["default"]},
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock")

    assert result.exit_code == 0, result.output
    assert "Locking environment: default" in result.output
    assert f"Wrote lockfile: {project_path / 'pylock.toml'}" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_global_lock_envs(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], **project.config.envs["default"]},
    )
    helpers.update_project_environment(project, "test", {"dependencies": ["pytest"]})

    # Set global lock-envs = true in [tool.hatch]
    project_file = project_path / "pyproject.toml"
    raw_config = load_toml_file(str(project_file))
    raw_config.setdefault("tool", {}).setdefault("hatch", {})["lock-envs"] = True

    with open(str(project_file), "w", encoding="utf-8") as f:
        f.write(tomli_w.dumps(raw_config))

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock")

    assert result.exit_code == 0, result.output
    assert "Locking environment: default" in result.output
    assert "Locking environment: test" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_per_env_override_global(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], **project.config.envs["default"]},
    )
    # test env explicitly opts out of locking
    helpers.update_project_environment(project, "test", {"dependencies": ["pytest"], "locked": False})

    # Set global lock-envs = true
    project_file = project_path / "pyproject.toml"
    raw_config = load_toml_file(str(project_file))
    raw_config.setdefault("tool", {}).setdefault("hatch", {})["lock-envs"] = True

    with open(str(project_file), "w", encoding="utf-8") as f:
        f.write(tomli_w.dumps(raw_config))

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock")

    assert result.exit_code == 0, result.output
    # default should be locked (global), test should NOT be locked (per-env override)
    assert "Locking environment: default" in result.output
    assert "Locking environment: test" not in result.output


@pytest.mark.usefixtures("mock_locker")
def test_named_env(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})
    helpers.update_project_environment(project, "test", {"dependencies": ["pytest"], "locked": True})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "test")

    assert result.exit_code == 0, result.output
    assert "Locking environment: test" in result.output
    assert f"Wrote lockfile: {project_path / 'pylock.test.toml'}" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_check_missing(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], "locked": True, **project.config.envs["default"]},
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "default", "--check")

    assert result.exit_code == 1
    assert "Lockfile does not exist" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_check_exists(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], "locked": True, **project.config.envs["default"]},
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        gen = hatch("env", "lock", "default")
        assert gen.exit_code == 0, gen.output
        result = hatch("env", "lock", "default", "--check")

    assert result.exit_code == 0, result.output
    assert "Lockfile is up to date" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_check_lockfile_stale(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], "locked": True, **project.config.envs["default"]},
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        assert hatch("env", "lock", "default").exit_code == 0
        (project_path / "pylock.toml").write_text("not-the-resolved-lock\n", encoding="utf-8")
        result = hatch("env", "lock", "default", "--check")

    assert result.exit_code == 1
    assert "not up to date" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_export(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], **project.config.envs["default"]},
    )

    custom_output = str(temp_dir / "custom-lock.toml")

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "default", "--export", custom_output)

    assert result.exit_code == 0, result.output
    assert f"Wrote lockfile: {custom_output}" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_export_all(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], **project.config.envs["default"]},
    )
    helpers.update_project_environment(project, "test", {"dependencies": ["pytest"]})

    export_dir = str(temp_dir / "locks")

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "--export-all", export_dir)

    assert result.exit_code == 0, result.output
    assert "Locking environment: default" in result.output
    assert "Locking environment: test" in result.output


@pytest.mark.usefixtures("helpers")
def test_export_and_export_all_mutually_exclusive(hatch, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    with project_path.as_cwd():
        result = hatch("env", "lock", "default", "--export", "a.toml", "--export-all", "locks/")

    assert result.exit_code == 1
    assert "Cannot use both" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_custom_lock_filename(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {
            "skip-install": True,
            "dependencies": ["requests"],
            "locked": True,
            "lock-filename": "locks/default.toml",
            **project.config.envs["default"],
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "default")

    assert result.exit_code == 0, result.output
    assert f"Wrote lockfile: {project_path / 'locks' / 'default.toml'}" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_matrix(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})
    helpers.update_project_environment(
        project,
        "test",
        {
            "dependencies": ["pytest"],
            "locked": True,
            "matrix": [{"version": ["9000", "42"]}],
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "test")

    assert result.exit_code == 0, result.output
    assert "Locking environment: test.9000" in result.output
    assert "Locking environment: test.42" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_matrix_incompatible(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})
    helpers.update_project_environment(
        project,
        "test",
        {
            "dependencies": ["pytest"],
            "locked": True,
            "matrix": [{"version": ["9000", "42"]}],
            "overrides": {"matrix": {"version": {"platforms": [{"value": "foo", "if": ["9000"]}]}}},
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "test")

    assert result.exit_code == 0, result.output
    assert "Locking environment: test.42" in result.output
    assert "Skipped 1 incompatible environment:" in result.output
    assert "test.9000 -> unsupported platform" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_shared_lock_filename_dedup(hatch, helpers, temp_dir, config_file):
    """When multiple matrix envs share the same lock-filename, generate once with merged deps."""
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})
    helpers.update_project_environment(
        project,
        "test",
        {
            "dependencies": ["pytest"],
            "locked": True,
            "lock-filename": "pylock.test.toml",
            "matrix": [{"version": ["9000", "42"]}],
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "test")

    assert result.exit_code == 0, result.output
    # Both envs share pylock.test.toml, so only one lockfile write should happen
    assert result.output.count("Wrote lockfile:") == 1
    assert f"Wrote lockfile: {project_path / 'pylock.test.toml'}" in result.output


def test_shared_lock_filename_different_python_errors(hatch, helpers, temp_dir, config_file):
    """When grouped envs have different Python versions, abort rather than generate an invalid lockfile."""
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})
    helpers.update_project_environment(
        project,
        "test",
        {
            "dependencies": ["pytest"],
            "locked": True,
            "lock-filename": "pylock.test.toml",
            "matrix": [{"python": ["3.12", "3.10"]}],
        },
    )

    with project_path.as_cwd():
        result = hatch("env", "lock", "test")

    assert result.exit_code == 1
    assert "target different Python versions" in result.output
    assert "lock-filename" in result.output


def test_plugin_dependencies_unmet(hatch, helpers, temp_dir, config_file, mock_plugin_installation):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    project = Project(project_path)
    helpers.update_project_environment(
        project, "default", {"skip-install": True, "locked": True, **project.config.envs["default"]}
    )

    dependency = os.urandom(16).hex()
    from hatchling.utils.constants import DEFAULT_CONFIG_FILE

    (project_path / DEFAULT_CONFIG_FILE).write_text(
        helpers.dedent(
            f"""
            [env]
            requires = ["{dependency}"]
            """
        )
    )

    with project_path.as_cwd():
        result = hatch("env", "lock", "default")

    assert result.exit_code == 0, result.output
    assert "Syncing environment plugin requirements" in result.output
    helpers.assert_plugin_installation(mock_plugin_installation, [dependency])


@pytest.mark.requires_internet
def test_lockfile_records_some_env_dependencies(hatch, helpers, temp_dir, config_file, uv_on_path):
    """End-to-end: ``tool.hatch.envs.<name>.dependencies`` are compiled into the on-disk lockfile."""
    _require_uv(uv_on_path)

    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})
    helpers.update_project_environment(
        project,
        "some-env",
        {
            "installer": "uv",
            "skip-install": True,
            "locked": True,
            "dependencies": ["click>=8.0"],
        },
    )

    lock_path = project_path / "pylock.some-env.toml"

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        assert hatch("env", "create", "some-env").exit_code == 0
        result = hatch("env", "lock", "some-env")

    assert result.exit_code == 0, (
        f"{result.output}\n{lock_path.read_text(encoding='utf-8') if lock_path.is_file() else '(no lockfile)'}"
    )
    assert lock_path.is_file()
    lock_body = lock_path.read_text(encoding="utf-8")
    assert "click" in lock_body.lower()


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_lockfile_resolves_git_revision_pin(hatch, helpers, temp_dir, config_file, uv_on_path):
    """End-to-end: a VCS dependency pinned to a specific revision is present in the generated lockfile."""
    _require_uv(uv_on_path)

    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})
    # Same pinned commit as ``tests/dep/test_sync.py::test_dependency_git_commit`` (short ref is resolvable).
    commit = "7f694b79e114c06fac5ec06019cada5a61e5570f"
    vcs_dep = f"requests @ git+https://github.com/psf/requests@{commit}"
    helpers.update_project_environment(
        project,
        "some-env",
        {
            "installer": "uv",
            "skip-install": True,
            "locked": True,
            "dependencies": [vcs_dep],
        },
    )

    lock_path = project_path / "pylock.some-env.toml"

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        assert hatch("env", "create", "some-env").exit_code == 0
        result = hatch("env", "lock", "some-env")

    assert result.exit_code == 0, (
        f"{result.output}\n{lock_path.read_text(encoding='utf-8') if lock_path.is_file() else '(no lockfile)'}"
    )
    assert lock_path.is_file()
    lock_body = lock_path.read_text(encoding="utf-8")
    assert "requests" in lock_body.lower()
    assert commit[:7] in lock_body


@pytest.mark.requires_internet
def test_lock_writes_one_lockfile_per_environment(hatch, helpers, temp_dir, config_file, uv_on_path):
    """
    Each locked Hatch environment maps to its own lockfile (``pylock.toml`` for ``default``,
    ``pylock.<name>.toml`` for others). A regression here would merge or drop environments.
    """
    _require_uv(uv_on_path)

    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"
    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    base = dict(project.config.envs["default"])
    helpers.update_project_environment(
        project,
        "default",
        {**base, "installer": "uv", "skip-install": True, "locked": True, "dependencies": ["httpx"]},
    )
    helpers.update_project_environment(
        project,
        "api",
        {"installer": "uv", "skip-install": True, "locked": True, "dependencies": ["click>=8.0"]},
    )
    helpers.update_project_environment(
        project,
        "worker",
        {"installer": "uv", "skip-install": True, "locked": True, "dependencies": ["rich"]},
    )

    lock_default = project_path / "pylock.toml"
    lock_api = project_path / "pylock.api.toml"
    lock_worker = project_path / "pylock.worker.toml"

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        for env in ("default", "api", "worker"):
            assert hatch("env", "create", env).exit_code == 0
        result = hatch("env", "lock")

    assert result.exit_code == 0, result.output
    assert lock_default.is_file()
    assert lock_api.is_file()
    assert lock_worker.is_file()

    assert "httpx" in lock_default.read_text(encoding="utf-8").lower()
    assert "click" in lock_api.read_text(encoding="utf-8").lower()
    assert "rich" in lock_worker.read_text(encoding="utf-8").lower()

    for path in (lock_default, lock_api, lock_worker):
        body = path.read_text(encoding="utf-8").lower()
        assert "sha256" in body, f"expected hashed lockfile from uv: {path}"


@pytest.mark.requires_internet
def test_lockfile_includes_optional_extra_dependencies(hatch, helpers, temp_dir, config_file, uv_on_path):
    """Layered ``uv pip compile`` must pass ``--extra`` so optional dependency groups appear in the lockfile."""
    _require_uv(uv_on_path)

    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"
    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    _patch_pyproject_metadata(project_path, optional_dependencies={"cli": ["binary"]})

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})
    helpers.update_project_environment(
        project,
        "with-extra",
        {
            **dict(project.config.envs["default"]),
            "installer": "uv",
            "skip-install": True,
            "locked": True,
            "features": ["cli"],
        },
    )

    lock_path = project_path / "pylock.with-extra.toml"

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        assert hatch("env", "create", "with-extra").exit_code == 0
        result = hatch("env", "lock", "with-extra")

    assert result.exit_code == 0, result.output
    body = lock_path.read_text(encoding="utf-8").lower()
    assert "binary" in body


@pytest.mark.requires_internet
def test_lockfile_includes_dependency_group_dependencies(hatch, helpers, temp_dir, config_file, uv_on_path):
    """``uv pip compile`` must receive ``--group`` so PEP 735 dependency groups are locked."""
    _require_uv(uv_on_path)

    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"
    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    _patch_pyproject_metadata(project_path, dependency_groups={"lint": ["binary"]})

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})
    helpers.update_project_environment(
        project,
        "with-group",
        {
            **dict(project.config.envs["default"]),
            "installer": "uv",
            "skip-install": True,
            "locked": True,
            "dependency-groups": ["lint"],
        },
    )

    lock_path = project_path / "pylock.with-group.toml"

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        assert hatch("env", "create", "with-group").exit_code == 0
        result = hatch("env", "lock", "with-group")

    assert result.exit_code == 0, result.output
    body = lock_path.read_text(encoding="utf-8").lower()
    assert "binary" in body


@pytest.mark.requires_internet
def test_lockfile_combines_env_dependencies_extra_and_group(hatch, helpers, temp_dir, config_file, uv_on_path):
    """One environment can lock env-only deps, a project extra, and a dependency group together."""
    _require_uv(uv_on_path)

    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"
    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    _patch_pyproject_metadata(
        project_path,
        optional_dependencies={"cli": ["charset-normalizer"]},
        dependency_groups={"qa": ["certifi"]},
    )

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})
    helpers.update_project_environment(
        project,
        "combo",
        {
            **dict(project.config.envs["default"]),
            "installer": "uv",
            "skip-install": True,
            "locked": True,
            "dependencies": ["urllib3"],
            "features": ["cli"],
            "dependency-groups": ["qa"],
        },
    )

    lock_path = project_path / "pylock.combo.toml"

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        assert hatch("env", "create", "combo").exit_code == 0
        result = hatch("env", "lock", "combo")

    assert result.exit_code == 0, result.output
    body = lock_path.read_text(encoding="utf-8").lower()
    assert "urllib3" in body
    assert "charset-normalizer" in body
    assert "certifi" in body


@pytest.mark.requires_internet
def test_lock_export_paths_use_same_names_as_export_all(hatch, helpers, temp_dir, config_file, uv_on_path):
    """
    Per-environment ``--export`` paths match the filenames ``--export-all`` uses (``pylock.toml`` for
    ``default``, ``pylock.<env>.toml`` otherwise). End-to-end ``--export-all`` is impractical here because it
    also locks internal environments (for example the version matrix for ``hatch-test``), which requires
    every matrix cell to exist.
    """
    _require_uv(uv_on_path)

    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"
    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()
    export_dir = temp_dir / "exported-locks"
    export_dir.mkdir()

    project = Project(project_path)
    base = dict(project.config.envs["default"])
    helpers.update_project_environment(
        project,
        "default",
        {**base, "installer": "uv", "skip-install": True, "locked": True, "dependencies": ["httpx"]},
    )
    helpers.update_project_environment(
        project,
        "sidecar",
        {"installer": "uv", "skip-install": True, "locked": True, "dependencies": ["click>=8.0"]},
    )

    exp_default = export_dir / "pylock.toml"
    exp_sidecar = export_dir / "pylock.sidecar.toml"

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        assert hatch("env", "create", "default").exit_code == 0
        assert hatch("env", "create", "sidecar").exit_code == 0
        r_default = hatch("env", "lock", "default", "--export", str(exp_default))
        r_sidecar = hatch("env", "lock", "sidecar", "--export", str(exp_sidecar))

    assert r_default.exit_code == 0, r_default.output
    assert r_sidecar.exit_code == 0, r_sidecar.output
    assert exp_default.is_file()
    assert exp_sidecar.is_file()
    assert "httpx" in exp_default.read_text(encoding="utf-8").lower()
    assert "click" in exp_sidecar.read_text(encoding="utf-8").lower()
