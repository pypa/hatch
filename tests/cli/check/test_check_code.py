from __future__ import annotations

import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.project.core import Project


def construct_ruff_defaults_file(rules: tuple[str, ...]) -> str:
    from hatch.cli.fmt.core import PER_FILE_IGNORED_RULES

    lines = [
        "line-length = 120",
        "",
        "[format]",
        "docstring-code-format = true",
        "docstring-code-line-length = 80",
        "",
        "[lint]",
    ]

    # Selected rules
    lines.append("select = [")
    lines.extend(f'  "{rule}",' for rule in sorted(rules))
    lines.extend(("]", ""))

    # Ignored rules
    lines.append("[lint.per-file-ignores]")
    for glob, ignored_rules in PER_FILE_IGNORED_RULES.items():
        lines.append(f'"{glob}" = [')
        lines.extend(f'  "{ignored_rule}",' for ignored_rule in ignored_rules)
        lines.append("]")

    # Default config
    lines.extend((
        "",
        "[lint.flake8-tidy-imports]",
        'ban-relative-imports = "all"',
        "",
        "[lint.isort]",
        'known-first-party = ["my_app"]',
        "",
        "[lint.flake8-pytest-style]",
        "fixture-parentheses = false",
        "mark-parentheses = false",
    ))

    # Ensure the file ends with a newline to satisfy other linters
    lines.append("")

    return "\n".join(lines)


@pytest.fixture(scope="module")
def defaults_file_stable() -> str:
    from hatch.cli.fmt.core import STABLE_RULES

    return construct_ruff_defaults_file(STABLE_RULES)


@pytest.fixture(scope="module")
def defaults_file_preview() -> str:
    from hatch.cli.fmt.core import PREVIEW_RULES, STABLE_RULES

    return construct_ruff_defaults_file(STABLE_RULES + PREVIEW_RULES)


class TestDefaultCheckMode:
    """Tests that `hatch check code` defaults to check-only (no fixes applied)."""

    def test_check_only(self, hatch, temp_dir, config_file, env_run, mocker, platform, defaults_file_stable):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        config_dir = data_path / "env" / ".internal" / "hatch-check-code" / ".config" / project_path.id
        default_config = config_dir / "ruff_defaults.toml"
        user_config = config_dir / "pyproject.toml"
        user_config_path = platform.join_command_args([str(user_config)])

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "code")

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call(f"ruff check --config {user_config_path} .", shell=True),
        ]

        assert default_config.read_text() == defaults_file_stable

    def test_fix(self, hatch, temp_dir, config_file, env_run, mocker, platform, defaults_file_stable):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        config_dir = data_path / "env" / ".internal" / "hatch-check-code" / ".config" / project_path.id
        default_config = config_dir / "ruff_defaults.toml"
        user_config = config_dir / "pyproject.toml"
        user_config_path = platform.join_command_args([str(user_config)])

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "code", "--fix")

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call(f"ruff check --config {user_config_path} --fix .", shell=True),
        ]

        assert default_config.read_text() == defaults_file_stable


class TestPreview:
    def test_preview_check(self, hatch, temp_dir, config_file, env_run, mocker, platform, defaults_file_preview):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        config_dir = data_path / "env" / ".internal" / "hatch-check-code" / ".config" / project_path.id
        default_config = config_dir / "ruff_defaults.toml"
        user_config = config_dir / "pyproject.toml"
        user_config_path = platform.join_command_args([str(user_config)])

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "code", "--", "--preview")

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call(f"ruff check --config {user_config_path} --preview .", shell=True),
        ]

        assert default_config.read_text() == defaults_file_preview

    def test_preview_fix(self, hatch, temp_dir, config_file, env_run, mocker, platform, defaults_file_preview):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        config_dir = data_path / "env" / ".internal" / "hatch-check-code" / ".config" / project_path.id
        default_config = config_dir / "ruff_defaults.toml"
        user_config = config_dir / "pyproject.toml"
        user_config_path = platform.join_command_args([str(user_config)])

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "code", "--fix", "--", "--preview")

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call(f"ruff check --config {user_config_path} --preview --fix .", shell=True),
        ]

        assert default_config.read_text() == defaults_file_preview


class TestArguments:
    def test_forwarding(self, hatch, temp_dir, config_file, env_run, mocker, platform, defaults_file_stable):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        config_dir = data_path / "env" / ".internal" / "hatch-check-code" / ".config" / project_path.id
        default_config = config_dir / "ruff_defaults.toml"
        user_config = config_dir / "pyproject.toml"
        user_config_path = platform.join_command_args([str(user_config)])

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "code", "--", "--foo", "bar")

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call(f"ruff check --config {user_config_path} --foo bar", shell=True),
        ]

        assert default_config.read_text() == defaults_file_stable


class TestConfigPath:
    @pytest.mark.usefixtures("env_run")
    def test_sync_without_config(self, hatch, helpers, temp_dir, config_file):
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
            result = hatch("check", "code", "--sync")

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            The --sync flag can only be used when the `tool.hatch.format.config-path` option is defined
            """
        )

    def test_sync(self, hatch, temp_dir, config_file, env_run, mocker, defaults_file_stable):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()
        default_config_file = project_path / "ruff_defaults.toml"
        assert not default_config_file.is_file()

        project = Project(project_path)
        config = dict(project.raw_config)
        config["tool"]["hatch"]["envs"] = {"hatch-check-code": {"config-path": "ruff_defaults.toml"}}
        config["tool"]["ruff"] = {"extend": "ruff_defaults.toml"}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "code", "--sync")

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / "env" / ".internal" / "hatch-check-code" / ".config"
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call("ruff check .", shell=True),
        ]

        assert default_config_file.read_text() == defaults_file_stable


class TestCustomScripts:
    def test_fix(self, hatch, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        project = Project(project_path)
        config = dict(project.raw_config)
        config["tool"]["hatch"]["envs"] = {
            "hatch-check-code": {
                "config-path": "none",
                "dependencies": ["flake8"],
                "scripts": {
                    "lint-check": "flake8 {args:.}",
                    "lint-fix": "flake8 --fix {args:.}",
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "code", "--fix")

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / "env" / ".internal" / "hatch-check-code" / ".config"
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call("flake8 --fix .", shell=True),
        ]

    def test_check(self, hatch, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins["default"]["tests"] = False
        config_file.save()

        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        project = Project(project_path)
        config = dict(project.raw_config)
        config["tool"]["hatch"]["envs"] = {
            "hatch-check-code": {
                "config-path": "none",
                "dependencies": ["flake8"],
                "scripts": {
                    "lint-check": "flake8 {args:.}",
                    "lint-fix": "flake8 --fix {args:.}",
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("check", "code")

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / "env" / ".internal" / "hatch-check-code" / ".config"
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call("flake8 .", shell=True),
        ]
