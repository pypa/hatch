from contextlib import contextmanager

import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.env.virtual import VirtualEnvironment
from hatch.project.core import Project
from hatch.utils.toml import load_toml_file


@pytest.mark.usefixtures("mock_locker")
def test_dep_lock_export(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], **project.config.envs["default"]},
    )

    custom_output = str(temp_dir / "dep-lock.toml")

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("dep", "lock", "--export", custom_output)

    assert result.exit_code == 0, result.output
    assert f"Wrote lockfile: {custom_output}" in result.output


@pytest.mark.usefixtures("mock_locker")
def test_top_level_lock_matches_dep_lock(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], **project.config.envs["default"]},
    )

    out_a = str(temp_dir / "via-dep.toml")
    out_b = str(temp_dir / "via-top.toml")

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        assert hatch("dep", "lock", "--export", out_a).exit_code == 0
        assert hatch("lock", "--export", out_b).exit_code == 0

    assert (temp_dir / "via-dep.toml").read_text() == (temp_dir / "via-top.toml").read_text()


@pytest.mark.usefixtures("mock_locker")
def test_dep_sync_succeeds_skipping_real_activation(hatch, helpers, temp_dir, config_file, mocker, uv_on_path):
    """``dep sync`` runs the locked path without a real venv layout (avoids hanging on activation)."""
    if not uv_on_path:
        pytest.skip("uv is not available")

    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    @contextmanager
    def skip_activation(_self):
        yield

    mocker.patch.object(VirtualEnvironment, "safe_activation", skip_activation)

    project_name = "My.App"

    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {
            **project.config.envs["default"],
            "skip-install": True,
            "dependencies": ["requests"],
            "locked": True,
            "installer": "uv",
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        assert hatch("dep", "lock").exit_code == 0
        result = hatch("dep", "sync")

    assert result.exit_code == 0, result.output
    assert "Synced environment" in result.output


def test_dep_sync_aborts_when_pip_locker_cannot_apply(hatch, helpers, temp_dir, config_file, mocker):
    @contextmanager
    def skip_activation(_self):
        yield

    mocker.patch.object(VirtualEnvironment, "safe_activation", skip_activation)

    stub_pylock = "lock-version = 1\n"

    def fake_generate(_environment, output_path, **_kwargs):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(stub_pylock, encoding="utf-8")

    mocker.patch("hatch.env.lock.generate_lockfile", side_effect=fake_generate)
    mocker.patch("hatch.env.virtual.VirtualEnvironment.exists", return_value=True)
    mocker.patch("hatch.env.virtual.VirtualEnvironment.dependency_hash", return_value="")
    mocker.patch("hatch.env.virtual.VirtualEnvironment.command_context")

    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {
            **project.config.envs["default"],
            "skip-install": True,
            "installer": "pip",
            "locker": "pip",
            "dependencies": ["requests"],
            "locked": True,
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        assert hatch("dep", "lock").exit_code == 0
        result = hatch("dep", "sync")

    assert result.exit_code == 1
    assert "Cannot sync environment `default` from lockfile" in result.output
    assert "Applying lockfiles with the pip locker is not yet supported." in result.output
    assert "Synced environment" not in result.output


def test_dep_sync_aborts_when_not_locked(hatch, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"

    with project_path.as_cwd():
        result = hatch("dep", "sync")

    assert result.exit_code == 1
    assert "not `locked`" in result.output


def test_dep_sync_aborts_without_lockfile(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], "locked": True, **project.config.envs["default"]},
    )

    with project_path.as_cwd():
        result = hatch("dep", "sync")

    assert result.exit_code == 1
    assert "No lockfile" in result.output


def test_unknown_locker_aborts(hatch, helpers, temp_dir, config_file, mocker):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    mocker.patch("hatch.env.virtual.VirtualEnvironment.exists", return_value=True)
    mocker.patch("hatch.env.virtual.VirtualEnvironment.dependency_hash", return_value="")
    mocker.patch("hatch.env.virtual.VirtualEnvironment.command_context")

    project_name = "My.App"

    with temp_dir.as_cwd():
        assert hatch("new", project_name).exit_code == 0

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        "default",
        {"skip-install": True, "dependencies": ["requests"], **project.config.envs["default"]},
    )

    path = project_path / "pyproject.toml"
    data = load_toml_file(str(path))
    data.setdefault("tool", {}).setdefault("hatch", {})["locker"] = "no-such-locker-plugin-xyz"
    import tomli_w

    path.write_text(tomli_w.dumps(data), encoding="utf-8")

    export_path = str(temp_dir / "out.toml")

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "lock", "default", "--export", export_path)

    assert result.exit_code == 1
    assert "Unknown locker plugin" in result.output
