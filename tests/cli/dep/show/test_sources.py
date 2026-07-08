import pytest

from hatch.project.core import Project
from hatch.utils.structures import EnvVars


@pytest.fixture(scope="module", autouse=True)
def _terminal_width():
    with EnvVars({"COLUMNS": "200"}):
        yield


def test_no_sources(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch("new", "My.App")

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    with project_path.as_cwd():
        result = hatch("dep", "show", "sources")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        No sources defined in `[tool.hatch.sources]`
        """
    )


def test_matched_and_unused(hatch, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch("new", "My.App")

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    project = Project(project_path)
    config = dict(project.raw_config)
    config["project"]["dependencies"] = ["dep1"]
    config.setdefault("tool", {}).setdefault("hatch", {})["sources"] = {
        "dep1": "./packages/dep1",
        "dep2": {"index": "https://pypi.example.com/simple"},
    }
    project.save_config(config)

    with project_path.as_cwd():
        result = hatch("dep", "show", "sources", "--ascii")

    assert result.exit_code == 0, result.output
    assert "Sources: default" in result.output
    assert "./packages/dep1" in result.output
    assert "https://pypi.example.com/simple" in result.output
    assert "Sources matched no dependencies of environment `default`: dep2" in result.output


def test_env_sources_override(hatch, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch("new", "My.App")

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"

    project = Project(project_path)
    config = dict(project.raw_config)
    config["project"]["dependencies"] = ["dep1"]
    hatch_config = config.setdefault("tool", {}).setdefault("hatch", {})
    hatch_config["sources"] = {"dep1": "./packages/dep1"}
    hatch_config.setdefault("envs", {})["default"] = {
        "sources": {"dep1": {"git": "https://example.com/dep1", "branch": "main"}},
    }
    project.save_config(config)

    with project_path.as_cwd():
        result = hatch("dep", "show", "sources", "--ascii")

    assert result.exit_code == 0, result.output
    assert "git+https://example.com/dep1@main" in result.output
    assert "./packages/dep1" not in result.output
