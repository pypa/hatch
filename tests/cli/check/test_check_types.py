from __future__ import annotations

from hatch.config.constants import ConfigEnvVars


class TestDefaults:
    def test_check(self, hatch, temp_dir, config_file, env_run):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "types")

        assert result.exit_code == 0, result.output
        assert not result.output

        # Pyrefly adds --config with auto-generated config path
        assert len(env_run.call_args_list) == 1
        command = env_run.call_args_list[0].args[0]
        assert command.startswith("pyrefly check --config ")

    def test_summarize(self, hatch, temp_dir, config_file, env_run):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "types", "--summarize")

        assert result.exit_code == 0, result.output
        assert not result.output

        assert len(env_run.call_args_list) == 1
        command = env_run.call_args_list[0].args[0]
        assert command.startswith("pyrefly check --config ")
        assert "--summarize-errors" in command

    def test_cover(self, hatch, temp_dir, config_file, env_run):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "types", "--cover")

        assert result.exit_code == 0, result.output
        assert not result.output

        assert len(env_run.call_args_list) == 1
        command = env_run.call_args_list[0].args[0]
        assert command.startswith("pyrefly report --config ")


class TestArguments:
    def test_forwarding(self, hatch, temp_dir, config_file, env_run):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "types", "--", "--foo", "bar")

        assert result.exit_code == 0, result.output
        assert not result.output

        assert len(env_run.call_args_list) == 1
        command = env_run.call_args_list[0].args[0]
        assert command.startswith("pyrefly check --config ")
        assert "--foo bar" in command
