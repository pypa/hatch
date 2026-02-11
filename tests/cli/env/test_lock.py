import os

import pytest
import tomli_w

from hatch.config.constants import ConfigEnvVars
from hatch.project.core import Project
from hatch.utils.toml import load_toml_file


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


@pytest.mark.usefixtures("env_run")
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


@pytest.mark.usefixtures("env_run")
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


@pytest.mark.usefixtures("env_run")
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


@pytest.mark.usefixtures("env_run")
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


@pytest.mark.usefixtures("env_run")
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


@pytest.mark.usefixtures("env_run")
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


@pytest.mark.usefixtures("env_run")
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

    # Create a lockfile to check against
    (project_path / "pylock.toml").write_text("")

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "default", "--check")

    assert result.exit_code == 0, result.output
    assert "Lockfile exists" in result.output


@pytest.mark.usefixtures("env_run")
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


@pytest.mark.usefixtures("env_run")
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


def test_export_and_export_all_mutually_exclusive(hatch, helpers, temp_dir, config_file):
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


@pytest.mark.usefixtures("env_run")
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


@pytest.mark.usefixtures("env_run")
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


@pytest.mark.usefixtures("env_run")
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


@pytest.mark.usefixtures("env_run")
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
