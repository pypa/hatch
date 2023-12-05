from __future__ import annotations

from subprocess import CompletedProcess

import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.env.internal.fmt import PER_FILE_IGNORED_RULES, PREVIEW_RULES, STABLE_RULES
from hatch.project.core import Project


def construct_ruff_defaults_file(rules: tuple[str, ...]) -> str:
    lines = ['line-length = 120', '', '[lint]']

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
    return construct_ruff_defaults_file(STABLE_RULES)


@pytest.fixture(scope='module')
def defaults_file_preview() -> str:
    return construct_ruff_defaults_file(STABLE_RULES + PREVIEW_RULES)


@pytest.fixture(scope='module', autouse=True)
def ruff_on_path():
    import shutil

    return shutil.which('ruff') or 'ruff'


class TestDefaults:
    def test_fix(self, hatch, temp_dir, config_file, mocker, ruff_on_path, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'check', '--config', str(user_config), '--fix', '.'],
                shell=False,
            ),
            mocker.call(
                [ruff_on_path, 'format', '--config', str(user_config), '.'],
                shell=False,
            ),
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

    def test_check(self, hatch, temp_dir, config_file, mocker, ruff_on_path, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--check')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'check', '--config', str(user_config), '.'],
                shell=False,
            ),
            mocker.call(
                [ruff_on_path, 'format', '--config', str(user_config), '--check', '--diff', '.'],
                shell=False,
            ),
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


class TestPreview:
    def test_fix_flag(self, hatch, temp_dir, config_file, mocker, ruff_on_path, defaults_file_preview):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--preview')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'check', '--config', str(user_config), '--fix', '--preview', '.'],
                shell=False,
            ),
            mocker.call(
                [ruff_on_path, 'format', '--config', str(user_config), '--preview', '.'],
                shell=False,
            ),
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

    def test_check_flag(self, hatch, temp_dir, config_file, mocker, ruff_on_path, defaults_file_preview):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--check', '--preview')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'check', '--config', str(user_config), '--preview', '.'],
                shell=False,
            ),
            mocker.call(
                [ruff_on_path, 'format', '--config', str(user_config), '--check', '--diff', '--preview', '.'],
                shell=False,
            ),
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

    def test_config_fallback_linter(self, hatch, temp_dir, config_file, mocker, ruff_on_path, defaults_file_preview):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        original_user_config = project_path / 'pyproject.toml'
        original_user_config.write_text(f'{original_user_config.read_text()}\n[tool.ruff.lint]\npreview = true')

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--check')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'check', '--config', str(user_config), '--preview', '.'],
                shell=False,
            ),
            mocker.call(
                [ruff_on_path, 'format', '--config', str(user_config), '--check', '--diff', '.'],
                shell=False,
            ),
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

    def test_config_fallback_formatter(self, hatch, temp_dir, config_file, mocker, ruff_on_path, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        original_user_config = project_path / 'pyproject.toml'
        original_user_config.write_text(f'{original_user_config.read_text()}\n[tool.ruff.format]\npreview = true')

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--check')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'check', '--config', str(user_config), '.'],
                shell=False,
            ),
            mocker.call(
                [ruff_on_path, 'format', '--config', str(user_config), '--check', '--diff', '--preview', '.'],
                shell=False,
            ),
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


class TestComponents:
    def test_only_linter(self, hatch, temp_dir, config_file, mocker, ruff_on_path, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--linter')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'check', '--config', str(user_config), '--fix', '.'],
                shell=False,
            ),
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

    def test_only_formatter(self, hatch, temp_dir, config_file, mocker, ruff_on_path, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--formatter')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'format', '--config', str(user_config), '.'],
                shell=False,
            ),
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

    def test_select_multiple(self, hatch, helpers, temp_dir, config_file, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--linter', '--formatter')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            Cannot specify both --linter and --formatter
            """
        )


class TestArguments:
    def test_forwarding(self, hatch, temp_dir, config_file, mocker, ruff_on_path, defaults_file_stable):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--', '--foo', 'bar')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        config_dir = next(root_data_path.iterdir())
        default_config = config_dir / 'ruff_defaults.toml'
        user_config = config_dir / 'pyproject.toml'

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'check', '--config', str(user_config), '--fix', '--foo', 'bar'],
                shell=False,
            ),
            mocker.call(
                [ruff_on_path, 'format', '--config', str(user_config), '--foo', 'bar'],
                shell=False,
            ),
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
    def test_sync_without_config(self, hatch, helpers, temp_dir, config_file, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--sync')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            The --sync flag can only be used when the `tool.hatch.format.config-path` option is defined
            """
        )

    def test_sync(self, hatch, temp_dir, config_file, mocker, ruff_on_path, defaults_file_stable):
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

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt', '--sync')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        assert not root_data_path.is_dir()

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'check', '--fix', '.'],
                shell=False,
            ),
            mocker.call(
                [ruff_on_path, 'format', '.'],
                shell=False,
            ),
        ]

        assert default_config_file.read_text() == defaults_file_stable

    def test_no_sync(self, hatch, temp_dir, config_file, mocker, ruff_on_path):
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
        config['tool']['hatch']['format'] = {'config-path': 'ruff_defaults.toml'}
        config['tool']['ruff'] = {'extend': 'ruff_defaults.toml'}
        project.save_config(config)

        run = mocker.patch('subprocess.run', return_value=CompletedProcess([], 0, stdout=b''))
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.exists', return_value=True)
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.dependency_hash', return_value='')
        mocker.patch('hatch.env.internal.fmt.InternalFormatEnvironment.command_context')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('fmt')

        assert result.exit_code == 0, result.output
        assert not result.output

        root_data_path = data_path / 'env' / '.internal' / 'fmt' / '.config'
        assert not root_data_path.is_dir()

        assert run.call_args_list == [
            mocker.call(
                [ruff_on_path, 'check', '--fix', '.'],
                shell=False,
            ),
            mocker.call(
                [ruff_on_path, 'format', '.'],
                shell=False,
            ),
        ]

        assert not default_config_file.read_text()
