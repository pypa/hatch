import os

from hatch.env.virtual import VirtualEnvironment
from hatch.project.core import Project


class TestExposeUv:
    def test_uv_enabled_and_available(self, isolation, isolated_data_dir, platform, global_application, mocker):
        config = {"project": {"name": "my_app", "version": "0.0.1"}}
        project = Project(isolation, config=config)
        env = VirtualEnvironment(
            isolation,
            project.metadata,
            "default",
            {"installer": "uv"},
            {},
            isolated_data_dir,
            isolated_data_dir,
            platform,
            0,
            global_application,
        )
        mocker.patch.object(env, "uv_path", "/custom/path/to/uv")

        assert "HATCH_UV" not in os.environ
        with env.expose_uv():
            assert os.environ.get("HATCH_UV") == "/custom/path/to/uv"
        assert "HATCH_UV" not in os.environ

    def test_uv_enabled_but_not_found(self, isolation, isolated_data_dir, platform, global_application, mocker):
        config = {"project": {"name": "my_app", "version": "0.0.1"}}
        project = Project(isolation, config=config)
        env = VirtualEnvironment(
            isolation,
            project.metadata,
            "default",
            {"installer": "uv"},
            {},
            isolated_data_dir,
            isolated_data_dir,
            platform,
            0,
            global_application,
        )
        mocker.patch.object(env, "uv_path", None)

        assert "HATCH_UV" not in os.environ
        # Must not raise TypeError: str expected, not NoneType
        with env.expose_uv():
            assert "HATCH_UV" not in os.environ
        assert "HATCH_UV" not in os.environ

    def test_uv_disabled(self, isolation, isolated_data_dir, platform, global_application, mocker):
        config = {"project": {"name": "my_app", "version": "0.0.1"}}
        project = Project(isolation, config=config)
        env = VirtualEnvironment(
            isolation,
            project.metadata,
            "default",
            {"installer": "pip"},
            {},
            isolated_data_dir,
            isolated_data_dir,
            platform,
            0,
            global_application,
        )
        mocker.patch.object(env, "use_uv", False)
        mocker.patch.object(env, "uv_path", "/custom/path/to/uv")

        assert not env.use_uv
        assert "HATCH_UV" not in os.environ
        with env.expose_uv():
            assert "HATCH_UV" not in os.environ
        assert "HATCH_UV" not in os.environ

    def test_commands_fallback_when_uv_path_none(
        self, isolation, isolated_data_dir, platform, global_application, mocker
    ):
        config = {"project": {"name": "my_app", "version": "0.0.1"}}
        project = Project(isolation, config=config)
        env = VirtualEnvironment(
            isolation,
            project.metadata,
            "default",
            {"installer": "uv"},
            {},
            isolated_data_dir,
            isolated_data_dir,
            platform,
            0,
            global_application,
        )
        mocker.patch.object(env, "uv_path", None)

        pip_install_cmd = env.construct_pip_install_command(["foo"])
        assert pip_install_cmd[0] == "uv"

        sync_cmd = env.uv_pip_sync_command(isolation / "requirements.txt")
        assert sync_cmd[0] == "uv"
