from __future__ import annotations

import pytest

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


class TestExtendInjection:
    @pytest.mark.usefixtures("env_run")
    def test_existing_extend_in_pyproject_not_duplicated(self, hatch, temp_dir, config_file):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        pyproject = project_path / "pyproject.toml"
        pyproject.write_text(pyproject.read_text() + '\n[tool.ruff]\nextend = "some_existing.toml"\n')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check")

        assert result.exit_code == 0, result.output

        for env_name in ("hatch-check-code", "hatch-check-fmt"):
            config_dir = data_path / "env" / ".internal" / env_name / ".config" / project_path.id
            internal_pyproject = config_dir / "pyproject.toml"
            assert internal_pyproject.is_file(), f"missing {internal_pyproject}"
            contents = internal_pyproject.read_text()
            assert contents.count("extend") == 1, (
                f"{env_name}: 'extend' appears {contents.count('extend')} times, expected 1"
            )

    @pytest.mark.usefixtures("env_run")
    def test_existing_ruff_toml_with_extend_not_duplicated(self, hatch, temp_dir, config_file):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        (project_path / "ruff.toml").write_text('extend = "some_existing.toml"\nline-length = 88\n')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check")

        assert result.exit_code == 0, result.output

        for env_name in ("hatch-check-code", "hatch-check-fmt"):
            config_dir = data_path / "env" / ".internal" / env_name / ".config" / project_path.id
            internal_ruff_toml = config_dir / "ruff.toml"
            assert internal_ruff_toml.is_file(), f"missing {internal_ruff_toml}"
            contents = internal_ruff_toml.read_text()
            assert contents.count("extend") == 1, (
                f"{env_name}: 'extend' appears {contents.count('extend')} times, expected 1"
            )
