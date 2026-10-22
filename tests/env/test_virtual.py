from contextlib import nullcontext

from hatch.env.lockers.uv import UvLocker
from hatch.env.virtual import VirtualEnvironment
from hatch.project.core import Project
from hatch.utils.fs import Path


def test_uv_pip_sync_command_python(isolation, isolated_data_dir, platform, global_application):
    config = {"project": {"name": "my_app", "version": "0.0.1"}}
    project = Project(isolation, config=config)
    environment = VirtualEnvironment(
        isolation,
        project.metadata,
        "default",
        {"python": "3.14t", **project.config.envs["default"]},
        {},
        isolated_data_dir,
        isolated_data_dir,
        platform,
        0,
        global_application,
    )
    cmd = environment.uv_pip_sync_command(Path("lock.txt"))
    assert "--python" in cmd
    assert cmd[cmd.index("--python") + 1] == "3.14t"
    assert "--python-version" not in cmd


def test_uv_locker_lock_command_python(isolation, isolated_data_dir, platform, global_application, mocker):
    config = {"project": {"name": "my_app", "version": "0.0.1"}}
    project = Project(isolation, config=config)
    environment = VirtualEnvironment(
        isolation,
        project.metadata,
        "default",
        {"python": "3.14t", **project.config.envs["default"]},
        {},
        isolated_data_dir,
        isolated_data_dir,
        platform,
        0,
        global_application,
    )
    mocker.patch.object(environment, "command_context", return_value=nullcontext())
    mock_check = mocker.patch.object(environment.platform, "check_command")
    UvLocker.generate(environment, [], Path("lock.txt"))
    assert mock_check.called
    cmd = mock_check.call_args[0][0]
    assert "--python" in cmd
    assert cmd[cmd.index("--python") + 1] == "3.14t"
    assert "--python-version" not in cmd
