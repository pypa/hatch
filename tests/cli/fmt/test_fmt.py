from __future__ import annotations

import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.project.core import Project


def construct_ruff_defaults_file(rules: tuple[str, ...]) -> str:
    from hatch.cli.fmt.core import PER_FILE_IGNORED_RULES

    lines = [
        'line-length = 120',
        '',
        '[format]',
        'docstring-code-format = true',
        'docstring-code-line-length = 80',
        '',
        '[lint]',
    ]

    # Selected rules
    lines.append('select = [')
    lines.extend(f'  "{rule}",' for rule in sorted(rules))
    lines.extend((']', ''))

    # Ignored rules
    lines.append('[lint.per-file-ignores]')
    for glob, ignored_rules in PER_FILE_IGNORED_RULES.items():
        lines.append(f'"{glob}" = [')
        lines.extend(f'  "{ignored_rule}",' for ignored_rule in ignored_rules)
        lines.append(']')

    # Default config
    lines.extend((
        '',
        '[lint.flake8-tidy-imports]',
        'ban-relative-imports = "all"',
        '',
        '[lint.isort]',
        'known-first-party = ["my_app"]',
        '',
        '[lint.flake8-pytest-style]',
        'fixture-parentheses = false',
        'mark-parentheses = false',
    ))

    # Ensure the file ends with a newline to satisfy other linters
    lines.append('')

    return '\n'.join(lines)


@pytest.fixture(scope='module')
def defaults_file_stable() -> str:
    from hatch.cli.fmt.core import STABLE_RULES

    return construct_ruff_defaults_file(STABLE_RULES)


@pytest.fixture(scope='module')
def defaults_file_preview() -> str:
    from hatch.cli.fmt.core import PREVIEW_RULES, STABLE_RULES

    return construct_ruff_defaults_file(STABLE_RULES + PREVIEW_RULES)


class TestDefaults:
    def test_fix(self, hatch, helpers, temp_dir, config_file, env_run, mocker, platform, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        config_dir = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config' / project_path.id
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'
        user_config_path = platform.join_command_args([str(user_config)])

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            cmd [1] | ruff check --config {user_config_path} --fix .
            cmd [2] | ruff format --config {user_config_path} .
            """
        )

        assert env_run.call_args_list == [
            mocker.call(f'ruff check --config {user_config_path} --fix .', shell=True),
            mocker.call(f'ruff format --config {user_config_path} .', shell=True),
        ]

        assert default_config.read_text() == defaults_file_stable

        old_contents = (project_path / 'pyproject.toml').read_text()
        config_path = str(default_config).replace('\\', '\\\\')
        assert (
            user_config.read_text()
            == f"""\
{old_contents}
[tool.ruff]
extend = "{config_path}\""""
        )

    def test_check(self, hatch, helpers, temp_dir, config_file, env_run, mocker, platform, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        config_dir = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config' / project_path.id
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'
        user_config_path = platform.join_command_args([str(user_config)])

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--check')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            cmd [1] | ruff check --config {user_config_path} .
            cmd [2] | ruff format --config {user_config_path} --check --diff .
            """
        )

        assert env_run.call_args_list == [
            mocker.call(f'ruff check --config {user_config_path} .', shell=True),
            mocker.call(f'ruff format --config {user_config_path} --check --diff .', shell=True),
        ]

        assert default_config.read_text() == defaults_file_stable

        old_contents = (project_path / 'pyproject.toml').read_text()
        config_path = str(default_config).replace('\\', '\\\\')
        assert (
            user_config.read_text()
            == f"""\
{old_contents}
[tool.ruff]
extend = "{config_path}\""""
        )

    def test_existing_config(
        self, hatch, helpers, temp_dir, config_file, env_run, mocker, platform, defaults_file_stable
    ):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        config_dir = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config' / project_path.id
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'
        user_config_path = platform.join_command_args([str(user_config)])

        project_file = project_path / 'pyproject.toml'
        old_contents = project_file.read_text()
        project_file.write_text(f'[tool.ruff]\n{old_contents}')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--check')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            cmd [1] | ruff check --config {user_config_path} .
            cmd [2] | ruff format --config {user_config_path} --check --diff .
            """
        )

        assert env_run.call_args_list == [
            mocker.call(f'ruff check --config {user_config_path} .', shell=True),
            mocker.call(f'ruff format --config {user_config_path} --check --diff .', shell=True),
        ]

        assert default_config.read_text() == defaults_file_stable

        config_path = str(default_config).replace('\\', '\\\\')
        assert (
            user_config.read_text()
            == f"""\
[tool.ruff]
extend = "{config_path}\"
{old_contents.rstrip()}"""
        )


class TestPreview:
    def test_fix_flag(self, hatch, helpers, temp_dir, config_file, env_run, mocker, platform, defaults_file_preview):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        config_dir = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config' / project_path.id
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'
        user_config_path = platform.join_command_args([str(user_config)])

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--preview')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            cmd [1] | ruff check --config {user_config_path} --preview --fix .
            cmd [2] | ruff format --config {user_config_path} --preview .
            """
        )

        assert env_run.call_args_list == [
            mocker.call(f'ruff check --config {user_config_path} --preview --fix .', shell=True),
            mocker.call(f'ruff format --config {user_config_path} --preview .', shell=True),
        ]

        assert default_config.read_text() == defaults_file_preview

        old_contents = (project_path / 'pyproject.toml').read_text()
        config_path = str(default_config).replace('\\', '\\\\')
        assert (
            user_config.read_text()
            == f"""\
{old_contents}
[tool.ruff]
extend = "{config_path}\""""
        )

    def test_check_flag(self, hatch, helpers, temp_dir, config_file, env_run, mocker, platform, defaults_file_preview):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        config_dir = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config' / project_path.id
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'
        user_config_path = platform.join_command_args([str(user_config)])

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--check', '--preview')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            cmd [1] | ruff check --config {user_config_path} --preview .
            cmd [2] | ruff format --config {user_config_path} --preview --check --diff .
            """
        )

        assert env_run.call_args_list == [
            mocker.call(f'ruff check --config {user_config_path} --preview .', shell=True),
            mocker.call(f'ruff format --config {user_config_path} --preview --check --diff .', shell=True),
        ]

        assert default_config.read_text() == defaults_file_preview

        old_contents = (project_path / 'pyproject.toml').read_text()
        config_path = str(default_config).replace('\\', '\\\\')
        assert (
            user_config.read_text()
            == f"""\
{old_contents}
[tool.ruff]
extend = "{config_path}\""""
        )


class TestComponents:
    def test_only_linter(self, hatch, temp_dir, config_file, env_run, mocker, platform, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--linter')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'
        user_config_path = platform.join_command_args([str(user_config)])

        assert env_run.call_args_list == [
            mocker.call(f'ruff check --config {user_config_path} --fix .', shell=True),
        ]

        assert default_config.read_text() == defaults_file_stable

        old_contents = (project_path / 'pyproject.toml').read_text()
        config_path = str(default_config).replace('\\', '\\\\')
        assert (
            user_config.read_text()
            == f"""\
{old_contents}
[tool.ruff]
extend = "{config_path}\""""
        )

    def test_only_formatter(self, hatch, temp_dir, config_file, env_run, mocker, platform, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--formatter')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'
        user_config_path = platform.join_command_args([str(user_config)])

        assert env_run.call_args_list == [
            mocker.call(f'ruff format --config {user_config_path} .', shell=True),
        ]

        assert default_config.read_text() == defaults_file_stable

        old_contents = (project_path / 'pyproject.toml').read_text()
        config_path = str(default_config).replace('\\', '\\\\')
        assert (
            user_config.read_text()
            == f"""\
{old_contents}
[tool.ruff]
extend = "{config_path}\""""
        )

    @pytest.mark.usefixtures('env_run')
    def test_select_multiple(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--linter', '--formatter')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            Cannot specify both --linter and --formatter
            """
        )


class TestArguments:
    def test_forwarding(self, hatch, helpers, temp_dir, config_file, env_run, mocker, platform, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        config_dir = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config' / project_path.id
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'
        user_config_path = platform.join_command_args([str(user_config)])

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--', '--foo', 'bar')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            cmd [1] | ruff check --config {user_config_path} --fix --foo bar
            cmd [2] | ruff format --config {user_config_path} --foo bar
            """
        )

        assert env_run.call_args_list == [
            mocker.call(f'ruff check --config {user_config_path} --fix --foo bar', shell=True),
            mocker.call(f'ruff format --config {user_config_path} --foo bar', shell=True),
        ]

        assert default_config.read_text() == defaults_file_stable

        old_contents = (project_path / 'pyproject.toml').read_text()
        config_path = str(default_config).replace('\\', '\\\\')
        assert (
            user_config.read_text()
            == f"""\
{old_contents}
[tool.ruff]
extend = "{config_path}\""""
        )


class TestConfigPath:
    @pytest.mark.usefixtures('env_run')
    def test_sync_without_config(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--sync')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            The --sync flag can only be used when the `tool.hatch.format.config-path` option is defined
            """
        )

    def test_sync(self, hatch, helpers, temp_dir, config_file, env_run, mocker, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()
        default_config_file = project_path / 'ruff_defaults.toml'
        assert not default_config_file.is_file()

        project = Project(project_path)
        config = dict(project.raw_config)
        config['tool']['hatch']['envs'] = {'hatch-static-analysis': {'config-path': 'ruff_defaults.toml'}}
        config['tool']['ruff'] = {'extend': 'ruff_defaults.toml'}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--sync')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            cmd [1] | ruff check --fix .
            cmd [2] | ruff format .
            """
        )

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call('ruff check --fix .', shell=True),
            mocker.call('ruff format .', shell=True),
        ]

        assert default_config_file.read_text() == defaults_file_stable

    def test_no_sync(self, hatch, helpers, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()
        default_config_file = project_path / 'ruff_defaults.toml'
        default_config_file.touch()

        project = Project(project_path)
        config = dict(project.raw_config)
        config['tool']['hatch']['envs'] = {'hatch-static-analysis': {'config-path': 'ruff_defaults.toml'}}
        config['tool']['ruff'] = {'extend': 'ruff_defaults.toml'}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            cmd [1] | ruff check --fix .
            cmd [2] | ruff format .
            """
        )

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call('ruff check --fix .', shell=True),
            mocker.call('ruff format .', shell=True),
        ]

        assert not default_config_file.read_text()

    def test_sync_legacy_config(self, hatch, helpers, temp_dir, config_file, env_run, mocker, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()
        default_config_file = project_path / 'ruff_defaults.toml'
        assert not default_config_file.is_file()

        project = Project(project_path)
        config = dict(project.raw_config)
        config['tool']['hatch']['format'] = {'config-path': 'ruff_defaults.toml'}
        config['tool']['ruff'] = {'extend': 'ruff_defaults.toml'}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--sync')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            The `tool.hatch.format.config-path` option is deprecated and will be removed in a future release. Use `tool.hatch.envs.hatch-static-analysis.config-path` instead.
            cmd [1] | ruff check --fix .
            cmd [2] | ruff format .
            """
        )

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call('ruff check --fix .', shell=True),
            mocker.call('ruff format .', shell=True),
        ]

        assert default_config_file.read_text() == defaults_file_stable


class TestCustomScripts:
    def test_only_linter_fix(self, hatch, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        project = Project(project_path)
        config = dict(project.raw_config)
        config['tool']['hatch']['envs'] = {
            'hatch-static-analysis': {
                'config-path': 'none',
                'dependencies': ['black', 'flake8', 'isort'],
                'scripts': {
                    'format-check': [
                        'black --check --diff {args:.}',
                        'isort --check-only --diff {args:.}',
                    ],
                    'format-fix': [
                        'isort {args:.}',
                        'black {args:.}',
                    ],
                    'lint-check': 'flake8 {args:.}',
                    'lint-fix': 'lint-check',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--linter')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call('flake8 .', shell=True),
        ]

    def test_only_linter_check(self, hatch, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        project = Project(project_path)
        config = dict(project.raw_config)
        config['tool']['hatch']['envs'] = {
            'hatch-static-analysis': {
                'config-path': 'none',
                'dependencies': ['black', 'flake8', 'isort'],
                'scripts': {
                    'format-check': [
                        'black --check --diff {args:.}',
                        'isort --check-only --diff {args:.}',
                    ],
                    'format-fix': [
                        'isort {args:.}',
                        'black {args:.}',
                    ],
                    'lint-check': 'flake8 {args:.}',
                    'lint-fix': 'lint-check',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--check', '--linter')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call('flake8 .', shell=True),
        ]

    def test_only_formatter_fix(self, hatch, helpers, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        project = Project(project_path)
        config = dict(project.raw_config)
        config['tool']['hatch']['envs'] = {
            'hatch-static-analysis': {
                'config-path': 'none',
                'dependencies': ['black', 'flake8', 'isort'],
                'scripts': {
                    'format-check': [
                        'black --check --diff {args:.}',
                        'isort --check-only --diff {args:.}',
                    ],
                    'format-fix': [
                        'isort {args:.}',
                        'black {args:.}',
                    ],
                    'lint-check': 'flake8 {args:.}',
                    'lint-fix': 'lint-check',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--formatter')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            cmd [1] | isort .
            cmd [2] | black .
            """
        )

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call('isort .', shell=True),
            mocker.call('black .', shell=True),
        ]

    def test_only_formatter_check(self, hatch, helpers, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        project = Project(project_path)
        config = dict(project.raw_config)
        config['tool']['hatch']['envs'] = {
            'hatch-static-analysis': {
                'config-path': 'none',
                'dependencies': ['black', 'flake8', 'isort'],
                'scripts': {
                    'format-check': [
                        'black --check --diff {args:.}',
                        'isort --check-only --diff {args:.}',
                    ],
                    'format-fix': [
                        'isort {args:.}',
                        'black {args:.}',
                    ],
                    'lint-check': 'flake8 {args:.}',
                    'lint-fix': 'lint-check',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--check', '--formatter')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            cmd [1] | black --check --diff .
            cmd [2] | isort --check-only --diff .
            """
        )

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call('black --check --diff .', shell=True),
            mocker.call('isort --check-only --diff .', shell=True),
        ]

    def test_fix(self, hatch, helpers, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        project = Project(project_path)
        config = dict(project.raw_config)
        config['tool']['hatch']['envs'] = {
            'hatch-static-analysis': {
                'config-path': 'none',
                'dependencies': ['black', 'flake8', 'isort'],
                'scripts': {
                    'format-check': [
                        'black --check --diff {args:.}',
                        'isort --check-only --diff {args:.}',
                    ],
                    'format-fix': [
                        'isort {args:.}',
                        'black {args:.}',
                    ],
                    'lint-check': 'flake8 {args:.}',
                    'lint-fix': 'lint-check',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            cmd [1] | flake8 .
            cmd [2] | isort .
            cmd [3] | black .
            """
        )

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call('flake8 .', shell=True),
            mocker.call('isort .', shell=True),
            mocker.call('black .', shell=True),
        ]

    def test_check(self, hatch, helpers, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        project = Project(project_path)
        config = dict(project.raw_config)
        config['tool']['hatch']['envs'] = {
            'hatch-static-analysis': {
                'config-path': 'none',
                'dependencies': ['black', 'flake8', 'isort'],
                'scripts': {
                    'format-check': [
                        'black --check --diff {args:.}',
                        'isort --check-only --diff {args:.}',
                    ],
                    'format-fix': [
                        'isort {args:.}',
                        'black {args:.}',
                    ],
                    'lint-check': 'flake8 {args:.}',
                    'lint-fix': 'lint-check',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--check')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            cmd [1] | flake8 .
            cmd [2] | black --check --diff .
            cmd [3] | isort --check-only --diff .
            """
        )

        root_data_path = data_path / 'env' / '.internal' / 'hatch-static-analysis' / '.config'
        assert not root_data_path.is_dir()

        assert env_run.call_args_list == [
            mocker.call('flake8 .', shell=True),
            mocker.call('black --check --diff .', shell=True),
            mocker.call('isort --check-only --diff .', shell=True),
        ]
