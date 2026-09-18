from __future__ import annotations

import os

import pytest

from hatch.dep.sync import Dependency


@pytest.fixture
def app(global_application):
    return global_application


class TestEnsurePluginDependencies:
    def test_uv_branch_orders_python_flag_after_subcommand(self, app, mocker):
        """uv rejects --python before the subcommand, so it must come after install."""
        mocker.patch("hatch.dep.sync.InstalledDistributions.dependencies_in_sync", return_value=False)
        mocker.patch("uv.find_uv_bin", return_value="/fake/uv")
        commands = []
        mocker.patch.object(app.platform, "check_command", side_effect=commands.append)

        app.ensure_plugin_dependencies([Dependency("foo")], wait_message="sync")

        assert commands == [
            [
                "/fake/uv",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--python",
                os.sys.executable,
                "-q",
                "foo",
            ]
        ]

    def test_pyapp_branch_orders_python_flag_before_subcommand(self, app, mocker):
        """pip requires --python before the subcommand name (#2389)."""
        mocker.patch.dict(
            os.environ,
            {"PYAPP": "/fake/app", "PYAPP_COMMAND_NAME": "fake-app"},
        )
        mocker.patch("hatch.dep.sync.InstalledDistributions.dependencies_in_sync", return_value=False)
        mocker.patch.object(app.platform, "check_command_output", return_value="/fake/python")
        commands = []

        def check_command(cmd, **kwargs):
            if kwargs.get("capture_output"):
                # Simulates the PythonInfo dep-check subprocess stdout.
                process = mocker.Mock()
                process.stdout = b"{'environment': {}, 'sys_path': []}"
                return process
            commands.append(cmd)
            return None

        mocker.patch.object(app.platform, "check_command", side_effect=check_command)

        app.ensure_plugin_dependencies([Dependency("foo")], wait_message="sync")

        assert commands == [
            [
                "/fake/app",
                "fake-app",
                "pip",
                "--python",
                os.sys.executable,
                "install",
                "--disable-pip-version-check",
                "-q",
                "foo",
            ]
        ]
