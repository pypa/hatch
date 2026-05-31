from __future__ import annotations

from hatch.config.constants import ConfigEnvVars


class TestNoSubcommand:
    """Tests that `hatch check` with no subcommand runs all checks."""

    def test_runs_all_checks(self, hatch, temp_dir, config_file, env_run):
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
            result = hatch("check")

        assert result.exit_code == 0, result.output

        # Should have run lint-check, format-check, and pyrefly check
        commands_run = [call.args[0] for call in env_run.call_args_list]
        assert any("ruff check" in cmd and "--fix" not in cmd for cmd in commands_run)
        assert any("ruff format" in cmd and "--check" in cmd for cmd in commands_run)
        assert any("pyrefly check" in cmd for cmd in commands_run)

    def test_runs_all_with_fix(self, hatch, temp_dir, config_file, env_run):
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
            result = hatch("check", "--fix")

        assert result.exit_code == 0, result.output

        # Should have run lint-fix, format-fix, and pyrefly check
        commands_run = [call.args[0] for call in env_run.call_args_list]
        assert any("ruff check" in cmd and "--fix" in cmd for cmd in commands_run)
        assert any("ruff format" in cmd and "--check" not in cmd for cmd in commands_run)
        assert any("pyrefly check" in cmd for cmd in commands_run)


class TestHelp:
    def test_help_output(self, hatch):
        result = hatch("check", "--help")

        assert result.exit_code == 0
        assert "code" in result.output
        assert "fmt" in result.output
        assert "types" in result.output
