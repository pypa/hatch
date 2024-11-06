from __future__ import annotations

import sys

import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.env.utils import get_env_var
from hatch.project.core import Project
from hatch.utils.structures import EnvVars


@pytest.fixture(scope='module', autouse=True)
def _terminal_width():
    with EnvVars({'COLUMNS': '100'}, exclude=[get_env_var(plugin_name='virtual', option='uv_path')]):
        yield


class TestDefaults:
    def test_basic(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly tests', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_arguments(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--', '--flag', '--', 'arg1', 'arg2')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly --flag -- arg1 arg2', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()


class TestArguments:
    def test_default_args(self, hatch, temp_dir, platform, config_file, env_run, mocker):
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
        config['tool']['hatch']['envs'] = {'hatch-test': {'default-args': ['tests1', 'foo bar', 'tests2']}}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test')

        assert result.exit_code == 0, result.output
        assert not result.output

        escape_char = '"' if platform.windows else "'"
        assert env_run.call_args_list == [
            mocker.call(f'pytest -p no:randomly tests1 {escape_char}foo bar{escape_char} tests2', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_args_override(self, hatch, temp_dir, config_file, env_run, mocker):
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
        config['tool']['hatch']['envs'] = {'hatch-test': {'default-args': ['tests1', 'foo bar', 'tests2']}}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test', '--', '--flag', '--', 'arg1', 'arg2')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly --flag -- arg1 arg2', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_extra_args(self, hatch, temp_dir, config_file, env_run, mocker):
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
        config['tool']['hatch']['envs'] = {'hatch-test': {'extra-args': ['-vv', '--print']}}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -vv --print -p no:randomly tests', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()


class TestCoverage:
    def test_flag(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--cover')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('coverage run -m pytest -p no:randomly tests', shell=True),
            mocker.call('coverage combine', shell=True),
            mocker.call('coverage report', shell=True),
        ]

        root_config_path = data_path / '.config' / 'coverage'
        config_dir = next(root_config_path.iterdir())
        coverage_config_file = next(config_dir.iterdir())

        assert coverage_config_file.read_text().strip().splitlines()[-2:] == [
            '[tool.coverage.run]',
            'parallel = true',
        ]

    def test_flag_with_arguments(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--cover', '--', '--flag', '--', 'arg1', 'arg2')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('coverage run -m pytest -p no:randomly --flag -- arg1 arg2', shell=True),
            mocker.call('coverage combine', shell=True),
            mocker.call('coverage report', shell=True),
        ]

        root_config_path = data_path / '.config' / 'coverage'
        config_dir = next(root_config_path.iterdir())
        coverage_config_file = next(config_dir.iterdir())

        assert coverage_config_file.read_text().strip().splitlines()[-2:] == [
            '[tool.coverage.run]',
            'parallel = true',
        ]

    def test_quiet_implicitly_enables(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--cover-quiet')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('coverage run -m pytest -p no:randomly tests', shell=True),
            mocker.call('coverage combine', shell=True),
        ]

        root_config_path = data_path / '.config' / 'coverage'
        config_dir = next(root_config_path.iterdir())
        coverage_config_file = next(config_dir.iterdir())

        assert coverage_config_file.read_text().strip().splitlines()[-2:] == [
            '[tool.coverage.run]',
            'parallel = true',
        ]

    def test_legacy_config_define_section(self, hatch, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        (project_path / '.coveragerc').touch()

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test', '--cover')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('coverage run -m pytest -p no:randomly tests', shell=True),
            mocker.call('coverage combine', shell=True),
            mocker.call('coverage report', shell=True),
        ]

        root_config_path = data_path / '.config' / 'coverage'
        config_dir = next(root_config_path.iterdir())
        coverage_config_file = next(config_dir.iterdir())

        assert coverage_config_file.read_text().strip().splitlines() == [
            '[run]',
            'parallel = true',
        ]

    def test_legacy_config_enable_parallel(self, hatch, temp_dir, config_file, env_run, mocker):
        config_file.model.template.plugins['default']['tests'] = False
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        data_path = temp_dir / 'data'
        data_path.mkdir()

        (project_path / '.coveragerc').write_text('[run]\nparallel = false\nbranch = true\n')

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test', '--cover')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('coverage run -m pytest -p no:randomly tests', shell=True),
            mocker.call('coverage combine', shell=True),
            mocker.call('coverage report', shell=True),
        ]

        root_config_path = data_path / '.config' / 'coverage'
        config_dir = next(root_config_path.iterdir())
        coverage_config_file = next(config_dir.iterdir())

        assert coverage_config_file.read_text().strip().splitlines() == [
            '[run]',
            'parallel = true',
            'branch = true',
        ]


class TestRandomize:
    def test_flag(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--randomize')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest tests', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_flag_with_arguments(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--randomize', '--', '--flag', '--', 'arg1', 'arg2')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest --flag -- arg1 arg2', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_config(self, hatch, temp_dir, config_file, env_run, mocker):
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
        config['tool']['hatch']['envs'] = {'hatch-test': {'randomize': True}}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest tests', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()


class TestParallel:
    def test_flag(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--parallel')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly -n logical tests', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_flag_with_arguments(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--parallel', '--', '--flag', '--', 'arg1', 'arg2')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly -n logical --flag -- arg1 arg2', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_config(self, hatch, temp_dir, config_file, env_run, mocker):
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
        config['tool']['hatch']['envs'] = {'hatch-test': {'parallel': True}}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly -n logical tests', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()


class TestRetries:
    def test_flag(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--retries', '2')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly -r aR --reruns 2 tests', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_flag_with_arguments(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--retries', '2', '--', '--flag', '--', 'arg1', 'arg2')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly -r aR --reruns 2 --flag -- arg1 arg2', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_config(self, hatch, temp_dir, config_file, env_run, mocker):
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
        config['tool']['hatch']['envs'] = {'hatch-test': {'retries': 2}}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly -r aR --reruns 2 tests', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()


class TestRetryDelay:
    @pytest.mark.usefixtures('env_run')
    def test_no_retries(self, hatch, temp_dir, config_file):
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
            result = hatch('test', '--retry-delay', '3.14')

        assert result.exit_code == 1, result.output
        assert result.output == 'The --retry-delay option requires the --retries option to be set as well.\n'

    def test_flag(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--retries', '2', '--retry-delay', '3.14')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly -r aR --reruns 2 --reruns-delay 3.14 tests', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_flag_with_arguments(self, hatch, temp_dir, config_file, env_run, mocker):
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
            result = hatch('test', '--retries', '2', '--retry-delay', '3.14', '--', '--flag', '--', 'arg1', 'arg2')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly -r aR --reruns 2 --reruns-delay 3.14 --flag -- arg1 arg2', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_config(self, hatch, temp_dir, config_file, env_run, mocker):
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
        config['tool']['hatch']['envs'] = {'hatch-test': {'retry-delay': 1.23}}
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test', '--retries', '2')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('pytest -p no:randomly -r aR --reruns 2 --reruns-delay 1.23 tests', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()


class TestCustomScripts:
    def test_basic(self, hatch, temp_dir, config_file, env_run, mocker):
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
            'hatch-test': {
                'scripts': {
                    'run': 'test',
                    'run-cov': 'test with coverage',
                    'cov-combine': 'combine coverage',
                    'cov-report': 'show coverage',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('test', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_coverage(self, hatch, temp_dir, config_file, env_run, mocker):
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
            'hatch-test': {
                'scripts': {
                    'run': 'test',
                    'run-cov': 'test with coverage',
                    'cov-combine': 'combine coverage',
                    'cov-report': 'show coverage',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test', '--cover')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call('test with coverage', shell=True),
            mocker.call('combine coverage', shell=True),
            mocker.call('show coverage', shell=True),
        ]

        root_config_path = data_path / '.config' / 'coverage'
        config_dir = next(root_config_path.iterdir())
        coverage_config_file = next(config_dir.iterdir())

        assert coverage_config_file.read_text().strip().splitlines()[-2:] == [
            '[tool.coverage.run]',
            'parallel = true',
        ]

    def test_single(self, hatch, temp_dir, config_file, env_run, mocker):
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
            'hatch-test': {
                'scripts': {
                    'run': 'test {env_name}',
                    'run-cov': 'test with coverage',
                    'cov-combine': 'combine coverage',
                    'cov-report': 'show coverage',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test')

        assert result.exit_code == 0, result.output
        assert not result.output

        assert env_run.call_args_list == [
            mocker.call(f'test hatch-test.py{".".join(map(str, sys.version_info[:2]))}', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_matrix(self, hatch, temp_dir, config_file, helpers, env_run, mocker):
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
            'hatch-test': {
                'matrix': [{'python': ['3.12', '3.10', '3.8']}],
                'scripts': {
                    'run': 'test {env_name}',
                    'run-cov': 'test with coverage',
                    'cov-combine': 'combine coverage',
                    'cov-report': 'show coverage',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test', '--all')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            ──────────────────────────────────────── hatch-test.py3.12 ─────────────────────────────────────────
            ──────────────────────────────────────── hatch-test.py3.10 ─────────────────────────────────────────
            ───────────────────────────────────────── hatch-test.py3.8 ─────────────────────────────────────────
            """
        )

        assert env_run.call_args_list == [
            mocker.call('test hatch-test.py3.12', shell=True),
            mocker.call('test hatch-test.py3.10', shell=True),
            mocker.call('test hatch-test.py3.8', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()


class TestFilters:
    @pytest.mark.usefixtures('env_run')
    @pytest.mark.parametrize('option', ['--include', '--exclude'])
    def test_usage_with_all(self, hatch, temp_dir, config_file, helpers, option):
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
            result = hatch('test', '--all', option, 'py=3.10')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            The --all option cannot be used with the --include or --exclude options.
            """
        )

    def test_include(self, hatch, temp_dir, config_file, helpers, env_run, mocker):
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
            'hatch-test': {
                'matrix': [{'python': ['3.12', '3.10', '3.8']}],
                'scripts': {
                    'run': 'test {env_name}',
                    'run-cov': 'test with coverage',
                    'cov-combine': 'combine coverage',
                    'cov-report': 'show coverage',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test', '-i', 'py=3.10')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            ──────────────────────────────────────── hatch-test.py3.10 ─────────────────────────────────────────
            """
        )

        assert env_run.call_args_list == [
            mocker.call('test hatch-test.py3.10', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_exclude(self, hatch, temp_dir, config_file, helpers, env_run, mocker):
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
            'hatch-test': {
                'matrix': [{'python': ['3.12', '3.10', '3.8']}],
                'scripts': {
                    'run': 'test {env_name}',
                    'run-cov': 'test with coverage',
                    'cov-combine': 'combine coverage',
                    'cov-report': 'show coverage',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test', '-x', 'py=3.10')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            ──────────────────────────────────────── hatch-test.py3.12 ─────────────────────────────────────────
            ───────────────────────────────────────── hatch-test.py3.8 ─────────────────────────────────────────
            """
        )

        assert env_run.call_args_list == [
            mocker.call('test hatch-test.py3.12', shell=True),
            mocker.call('test hatch-test.py3.8', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()

    def test_python(self, hatch, temp_dir, config_file, helpers, env_run, mocker):
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
            'hatch-test': {
                'matrix': [{'python': ['3.12', '3.10', '3.8']}],
                'scripts': {
                    'run': 'test {env_name}',
                    'run-cov': 'test with coverage',
                    'cov-combine': 'combine coverage',
                    'cov-report': 'show coverage',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test', '-py', '3.10')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            ──────────────────────────────────────── hatch-test.py3.10 ─────────────────────────────────────────
            """
        )

        assert env_run.call_args_list == [
            mocker.call('test hatch-test.py3.10', shell=True),
        ]

        assert not (data_path / '.config' / 'coverage').exists()


class TestShow:
    def test_default_compact(self, hatch, temp_dir, config_file, helpers):
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
            'hatch-test': {
                'matrix': [{'python': ['3.12', '3.10', '3.8']}],
                'dependencies': ['foo', 'bar'],
                'scripts': {
                    'run': 'test {env_name}',
                    'run-cov': 'test with coverage',
                    'cov-combine': 'combine coverage',
                    'cov-report': 'show coverage',
                },
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('test', '--show')

        assert result.exit_code == 0, result.output
        assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
            """
            +------------+---------+-------------------+--------------+-------------+
            | Name       | Type    | Envs              | Dependencies | Scripts     |
            +============+=========+===================+==============+=============+
            | hatch-test | virtual | hatch-test.py3.12 | bar          | cov-combine |
            |            |         | hatch-test.py3.10 | foo          | cov-report  |
            |            |         | hatch-test.py3.8  |              | run         |
            |            |         |                   |              | run-cov     |
            +------------+---------+-------------------+--------------+-------------+
            """
        )

    def test_verbose(self, hatch, temp_dir, config_file, helpers):
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
            'hatch-test': {
                'matrix': [{'python': ['3.12', '3.10', '3.8']}],
                'dependencies': ['foo', 'bar'],
                'scripts': {
                    'run': 'test {env_name}',
                    'run-cov': 'test with coverage',
                    'cov-combine': 'combine coverage',
                    'cov-report': 'show coverage',
                },
                'overrides': {'matrix': {'python': {'description': {'value': 'test 3.10', 'if': ['3.10']}}}},
            }
        }
        project.save_config(config)

        with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch('-v', 'test', '--show')

        assert result.exit_code == 0, result.output
        assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
            """
            +-------------------+---------+--------------+-------------+-------------+
            | Name              | Type    | Dependencies | Scripts     | Description |
            +===================+=========+==============+=============+=============+
            | hatch-test.py3.12 | virtual | bar          | cov-combine |             |
            |                   |         | foo          | cov-report  |             |
            |                   |         |              | run         |             |
            |                   |         |              | run-cov     |             |
            +-------------------+---------+--------------+-------------+-------------+
            | hatch-test.py3.10 | virtual | bar          | cov-combine | test 3.10   |
            |                   |         | foo          | cov-report  |             |
            |                   |         |              | run         |             |
            |                   |         |              | run-cov     |             |
            +-------------------+---------+--------------+-------------+-------------+
            | hatch-test.py3.8  | virtual | bar          | cov-combine |             |
            |                   |         | foo          | cov-report  |             |
            |                   |         |              | run         |             |
            |                   |         |              | run-cov     |             |
            +-------------------+---------+--------------+-------------+-------------+
            """
        )
