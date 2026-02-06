import os

import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.project.core import Project


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


def test_no_dependencies(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})

    with project_path.as_cwd():
        result = hatch("env", "lock")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Environment `default` has no dependencies to lock
        """
    )


@pytest.mark.usefixtures("env_run")
def test_default_env(hatch, helpers, temp_dir, config_file):
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

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock")

    assert result.exit_code == 0, result.output
    assert "Locking environment: default" in result.output
    assert f"Wrote lockfile: {project_path / 'pylock.toml'}" in result.output


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
    helpers.update_project_environment(project, "test", {"dependencies": ["pytest"]})

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
        {"skip-install": True, "dependencies": ["requests"], **project.config.envs["default"]},
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "--check")

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
        {"skip-install": True, "dependencies": ["requests"], **project.config.envs["default"]},
    )

    # Create a lockfile to check against
    (project_path / "pylock.toml").write_text("")

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "--check")

    assert result.exit_code == 0, result.output
    assert "Lockfile exists" in result.output


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
            "lock-filename": "locks/default.toml",
            **project.config.envs["default"],
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock")

    assert result.exit_code == 0, result.output
    assert f"Wrote lockfile: {project_path / 'locks' / 'default.toml'}" in result.output


@pytest.mark.usefixtures("env_run")
def test_output_option(hatch, helpers, temp_dir, config_file):
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
        result = hatch("env", "lock", "-o", custom_output)

    assert result.exit_code == 0, result.output
    assert f"Wrote lockfile: {custom_output}" in result.output


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


def test_plugin_dependencies_unmet(hatch, helpers, temp_dir, config_file, mock_plugin_installation):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})

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
        result = hatch("env", "lock")

    assert result.exit_code == 0, result.output
    assert "Syncing environment plugin requirements" in result.output
    helpers.assert_plugin_installation(mock_plugin_installation, [dependency])
