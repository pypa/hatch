from contextlib import nullcontext

from hatch.env.virtual import VirtualEnvironment
from hatch.project.core import Project


def test_locked_sync_installs_local_project_after_applying_lock(
    temp_dir, isolated_data_dir, platform, temp_application, mocker
):
    config = {
        "project": {"name": "my-app", "version": "0.0.1"},
        "tool": {
            "hatch": {
                "envs": {
                    "default": {
                        "installer": "uv",
                        "locked": True,
                        "skip-install": False,
                        "dev-mode": True,
                    }
                }
            }
        },
    }
    project = Project(temp_dir, config=config)
    project.set_app(temp_application)
    temp_application.project = project
    environment = VirtualEnvironment(
        temp_dir,
        project.metadata,
        "default",
        project.config.envs["default"],
        {},
        isolated_data_dir,
        isolated_data_dir,
        platform,
        0,
        temp_application,
    )
    assert not environment.workspace.members

    (temp_dir / "pylock.toml").write_text("lock-version = 1\n", encoding="utf-8")

    events = []
    mocker.patch.object(environment, "safe_activation", return_value=nullcontext())
    mocker.patch.object(
        platform,
        "check_command",
        side_effect=lambda command: events.append(("install", command)),
    )
    mocker.patch(
        "hatch.env.lock.apply_lock_with_locker",
        side_effect=lambda *_args: events.append(("lock", None)),
    )

    environment.sync_dependencies()

    assert [event for event, _ in events] == ["lock", "install"]
    install_command = events[1][1]
    assert install_command[-3:] == ["--no-deps", "--editable", temp_dir]
