import os

import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.project.core import Project
from hatchling.utils.constants import DEFAULT_CONFIG_FILE

pytestmark = [pytest.mark.usefixtures("mock_backend_process_output")]


def read_readme(project_dir):
    return repr((project_dir / "README.txt").read_text())[1:-1]


def test_other_backend(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    (path / "README.md").replace(path / "README.txt")

    project = Project(path)
    config = dict(project.raw_config)
    config["build-system"]["requires"] = ["flit-core==3.10.1"]
    config["build-system"]["build-backend"] = "flit_core.buildapi"
    config["project"]["version"] = "0.0.1"
    config["project"]["dynamic"] = []
    config["project"]["readme"] = "README.txt"
    del config["project"]["license"]
    project.save_config(config)

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("project", "metadata")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        {{
            "name": "my-app",
            "version": "0.0.1",
            "readme": {{
                "content-type": "text/plain",
                "text": "{read_readme(path)}\\n"
            }},
            "keywords": [
                ""
            ],
            "classifiers": [
                "Development Status :: 4 - Beta",
                "Programming Language :: Python",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
                "Programming Language :: Python :: 3.12",
                "Programming Language :: Python :: Implementation :: CPython",
                "Programming Language :: Python :: Implementation :: PyPy"
            ],
            "urls": {{
                "Documentation": "https://github.com/Foo Bar/my-app#readme",
                "Issues": "https://github.com/Foo Bar/my-app/issues",
                "Source": "https://github.com/Foo Bar/my-app"
            }},
            "authors": [
                {{
                    "email": "foo@bar.baz",
                    "name": "Foo Bar"
                }}
            ],
            "requires-python": ">=3.8"
        }}
        """
    )


def test_default_all(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    (path / "README.md").replace(path / "README.txt")

    project = Project(path)
    config = dict(project.raw_config)
    config["project"]["readme"] = "README.txt"
    project.save_config(config)

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("project", "metadata")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        {{
            "name": "my-app",
            "version": "0.0.1",
            "readme": {{
                "content-type": "text/plain",
                "text": "{read_readme(path)}"
            }},
            "requires-python": ">=3.8",
            "license": "MIT",
            "authors": [
                {{
                    "name": "Foo Bar",
                    "email": "foo@bar.baz"
                }}
            ],
            "classifiers": [
                "Development Status :: 4 - Beta",
                "Programming Language :: Python",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
                "Programming Language :: Python :: 3.12",
                "Programming Language :: Python :: Implementation :: CPython",
                "Programming Language :: Python :: Implementation :: PyPy"
            ],
            "urls": {{
                "Documentation": "https://github.com/Foo Bar/my-app#readme",
                "Issues": "https://github.com/Foo Bar/my-app/issues",
                "Source": "https://github.com/Foo Bar/my-app"
            }}
        }}
        """
    )


def test_field_readme(hatch, temp_dir):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    (path / "README.md").replace(path / "README.txt")

    project = Project(path)
    config = dict(project.raw_config)
    config["project"]["readme"] = "README.txt"
    project.save_config(config)

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("project", "metadata", "readme")

    assert result.exit_code == 0, result.output
    assert result.output == (
        f"""\
Creating environment: hatch-build
Checking dependencies
Syncing dependencies
Inspecting build dependencies
{(path / "README.txt").read_text()}
"""
    )


def test_field_string(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("project", "metadata", "license")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        MIT
        """
    )


def test_field_complex(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("project", "metadata", "urls")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        {
            "Documentation": "https://github.com/Foo Bar/my-app#readme",
            "Issues": "https://github.com/Foo Bar/my-app/issues",
            "Source": "https://github.com/Foo Bar/my-app"
        }
        """
    )


@pytest.mark.allow_backend_process
def test_incompatible_environment(hatch, temp_dir, helpers, build_env_config):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(path)
    helpers.update_project_environment(project, "hatch-build", {"python": "9000", **build_env_config})

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("project", "metadata")

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Environment `hatch-build` is incompatible: cannot locate Python: 9000
        """
    )


def test_plugin_dependencies_unmet(hatch, temp_dir, helpers, mock_plugin_installation):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

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

    (path / "README.md").replace(path / "README.txt")

    project = Project(path)
    config = dict(project.raw_config)
    config["project"]["readme"] = "README.txt"
    project.save_config(config)

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("project", "metadata")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Syncing environment plugin requirements
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        {{
            "name": "my-app",
            "version": "0.0.1",
            "readme": {{
                "content-type": "text/plain",
                "text": "{read_readme(path)}"
            }},
            "requires-python": ">=3.8",
            "license": "MIT",
            "authors": [
                {{
                    "name": "Foo Bar",
                    "email": "foo@bar.baz"
                }}
            ],
            "classifiers": [
                "Development Status :: 4 - Beta",
                "Programming Language :: Python",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
                "Programming Language :: Python :: 3.12",
                "Programming Language :: Python :: Implementation :: CPython",
                "Programming Language :: Python :: Implementation :: PyPy"
            ],
            "urls": {{
                "Documentation": "https://github.com/Foo Bar/my-app#readme",
                "Issues": "https://github.com/Foo Bar/my-app/issues",
                "Source": "https://github.com/Foo Bar/my-app"
            }}
        }}
        """
    )
    helpers.assert_plugin_installation(mock_plugin_installation, [dependency])


def test_build_dependencies_unmet(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    (path / "README.md").replace(path / "README.txt")

    project = Project(path)
    config = dict(project.raw_config)
    config["project"]["readme"] = "README.txt"
    config["tool"]["hatch"]["build"] = {"dependencies": ["binary"]}
    project.save_config(config)

    with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("project", "metadata", "license")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        Syncing dependencies
        MIT
        """
    )


@pytest.mark.allow_backend_process
@pytest.mark.requires_internet
def test_no_compatibility_check_if_exists(hatch, temp_dir, helpers, mocker):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    config = dict(project.raw_config)
    config["build-system"]["requires"].append("binary")
    project.save_config(config)

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("project", "metadata", "license")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        MIT
        """
    )

    mocker.patch("hatch.env.virtual.VirtualEnvironment.check_compatibility", side_effect=Exception("incompatible"))
    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("project", "metadata", "license")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Inspecting build dependencies
        MIT
        """
    )
