import os

import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.project.core import Project
from hatchling.utils.constants import DEFAULT_CONFIG_FILE


class TestNoProject:
    def test_random_directory(self, hatch, temp_dir, helpers):
        with temp_dir.as_cwd():
            result = hatch("version")

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            No project detected
            """
        )

    def test_configured_project(self, hatch, temp_dir, helpers, config_file):
        project = "foo"
        config_file.model.mode = "project"
        config_file.model.project = project
        config_file.model.projects = {project: str(temp_dir)}
        config_file.save()

        with temp_dir.as_cwd():
            result = hatch("version")

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            Project foo (not a project)
            """
        )


def test_other_backend_show(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    (path / "src" / "my_app" / "__init__.py").write_text('__version__ = "9000.42"')

    project = Project(path)
    config = dict(project.raw_config)
    config["build-system"]["requires"] = ["flit-core"]
    config["build-system"]["build-backend"] = "flit_core.buildapi"
    del config["project"]["license"]
    project.save_config(config)

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        9000.42
        """
    )


def test_other_backend_set(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(path)
    config = dict(project.raw_config)
    config["build-system"]["requires"] = ["flit-core"]
    config["build-system"]["build-backend"] = "flit_core.buildapi"
    del config["project"]["license"]
    project.save_config(config)

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version", "1.0.0")

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        The version can only be set when Hatchling is the build backend
        """
    )


def test_incompatible_environment(hatch, temp_dir, helpers, build_env_config):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(path)
    config = dict(project.raw_config)
    config["build-system"]["requires"].append("foo")
    project.save_config(config)
    helpers.update_project_environment(project, "hatch-build", {"python": "9000", **build_env_config})

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version")

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Environment `hatch-build` is incompatible: cannot locate Python: 9000
        """
    )


@pytest.mark.requires_internet
@pytest.mark.usefixtures("mock_backend_process")
def test_show_dynamic(hatch, helpers, temp_dir):
    project_name = "My.App"

    with temp_dir.as_cwd():
        hatch("new", project_name)

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        0.0.1
        """
    )


@pytest.mark.requires_internet
@pytest.mark.usefixtures("mock_backend_process")
def test_plugin_dependencies_unmet(hatch, helpers, temp_dir, mock_plugin_installation):
    project_name = "My.App"

    with temp_dir.as_cwd():
        hatch("new", project_name)

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    dependency = os.urandom(16).hex()
    (path / DEFAULT_CONFIG_FILE).write_text(
        helpers.dedent(
            f"""
            [env]
            requires = ["{dependency}"]
            """
        )
    )

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Syncing environment plugin requirements
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        0.0.1
        """
    )
    helpers.assert_plugin_installation(mock_plugin_installation, [dependency])


@pytest.mark.requires_internet
@pytest.mark.usefixtures("mock_backend_process")
def test_no_compatibility_check_if_exists(hatch, helpers, temp_dir, mocker):
    project_name = "My.App"

    with temp_dir.as_cwd():
        hatch("new", project_name)

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    config = dict(project.raw_config)
    config["build-system"]["requires"].append("binary")
    project.save_config(config)

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        0.0.1
        """
    )

    mocker.patch("hatch.env.virtual.VirtualEnvironment.check_compatibility", side_effect=Exception("incompatible"))
    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Inspecting build dependencies
        0.0.1
        """
    )


@pytest.mark.requires_internet
@pytest.mark.usefixtures("mock_backend_process")
def test_set_dynamic(hatch, helpers, temp_dir):
    project_name = "My.App"

    with temp_dir.as_cwd():
        hatch("new", project_name)

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version", "minor,rc")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        Old: 0.0.1
        New: 0.1.0rc0
        """
    )

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Inspecting build dependencies
        0.1.0rc0
        """
    )


@pytest.mark.requires_internet
@pytest.mark.usefixtures("mock_backend_process")
def test_set_dynamic_downgrade(hatch, helpers, temp_dir):
    project_name = "My.App"

    with temp_dir.as_cwd():
        hatch("new", project_name)

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    (path / "src" / "my_app" / "__about__.py").write_text('__version__ = "21.1.2"')

    # This one fails, because it's a downgrade without --force
    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version", "21.1.0", catch_exceptions=True)

    assert result.exit_code == 1, result.output
    assert str(result.exception) == "Version `21.1.0` is not higher than the original version `21.1.2`"

    # Try again, this time with --force
    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version", "--force", "21.1.0")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Inspecting build dependencies
        Old: 21.1.2
        New: 21.1.0
        """
    )

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Inspecting build dependencies
        21.1.0
        """
    )


def test_show_static(hatch, temp_dir):
    project_name = "My.App"

    with temp_dir.as_cwd():
        hatch("new", project_name)

    path = temp_dir / "my-app"

    project = Project(path)
    config = dict(project.raw_config)
    config["project"]["version"] = "1.2.3"
    config["project"]["dynamic"].remove("version")
    config["tool"]["hatch"]["metadata"] = {"hooks": {"foo": {}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch("version")

    assert result.exit_code == 0, result.output
    assert result.output == "1.2.3\n"


def test_set_static(hatch, helpers, temp_dir):
    project_name = "My.App"
    test_comment = "# This is a test comment to assure version bumps do not erase comments."

    with temp_dir.as_cwd():
        hatch("new", project_name)

    path = temp_dir / "my-app"
    pyproject = path / "pyproject.toml"
    data_path = temp_dir / "data"
    data_path.mkdir()

    # To test if formatting and comments are preserved after static set
    # Regular Project.save_config does not preserve it
    with open(pyproject, "r+", encoding="utf-8") as f:
        lines = list(f)
        for i, line in enumerate(lines):
            if line.startswith("dynamic"):
                lines[i] = 'version    =    "1.2.3"\n'
        lines.append(test_comment)
        f.seek(0)
        f.writelines(lines)

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version", "minor,rc")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Old: 1.2.3
        New: 1.3.0rc0
        """
    )

    project = Project(path)
    assert project.raw_config["project"]["version"] == "1.3.0rc0", "should update static version"

    with open(pyproject, encoding="utf-8") as fr:
        for line in fr:
            if line.startswith("version"):
                version_line = line
        last_line = line
    assert version_line == 'version    =    "1.3.0rc0"\n', "should preserve pyproject formatting"
    assert last_line == test_comment, "should preserve pyproject comments"


def test_set_static_downgrade(hatch, helpers, temp_dir):
    project_name = "My.App"

    with temp_dir.as_cwd():
        hatch("new", project_name)

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(path)
    config = dict(project.raw_config)
    config["project"]["version"] = "1.2.3"
    config["project"]["dynamic"].remove("version")
    project.save_config(config)

    # This one fails, because it's a downgrade without --force
    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version", "1.2.0", catch_exceptions=True)

    assert result.exit_code == 1, result.output
    assert str(result.exception) == "Version `1.2.0` is not higher than the original version `1.2.3`"

    # Try again, this time with --force
    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("version", "--force", "1.2.0")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Old: 1.2.3
        New: 1.2.0
        """
    )

    project = Project(path)
    assert project.raw_config["project"]["version"] == "1.2.0", "should force update static version"


@pytest.mark.requires_internet
@pytest.mark.usefixtures("mock_backend_process")
def test_verbose_output_to_stderr(hatch, temp_dir):
    """Test that verbose output (command display and status messages) goes to stderr, not stdout."""
    project_name = "My.App"

    with temp_dir.as_cwd():
        hatch("new", project_name)

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    # Run with verbose flag (-v) and separate stderr from stdout
    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("-v", "version")

    assert result.exit_code == 0, result.output

    # The actual version should be in stdout
    assert result.stdout == "0.0.1\n"

    # Verbose output should be in stderr
    assert "Inspecting build dependencies" in result.stderr
    assert "cmd [1] | python -u -m hatchling version" in result.stderr

    # These should NOT be in stdout
    assert "Inspecting build dependencies" not in result.stdout
    assert "cmd [1]" not in result.stdout
