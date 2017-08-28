import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, load_settings, restore_settings,
    save_settings
)
from hatch.utils import remove_path, temp_chdir, temp_move_path
from hatch.venv import VENV_DIR


def test_help():
    with temp_chdir():
        runner = CliRunner()
        result = runner.invoke(hatch, ['shed'])

        assert 'hatch shed' in result.output


def test_pyname_config_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['shed', '-p', 'python'])

        assert result.exit_code == 1
        assert 'Unable to locate config file. Try `hatch config --restore`.' in result.output


def test_pyname():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['pythons']['pyname'] = 'pypath'
            save_settings(settings)
            result = runner.invoke(hatch, ['shed', '-p', 'pyname'])
            assert load_settings()['pythons'] == {}

        assert result.exit_code == 0
        assert 'Successfully removed Python path named `pyname`.' in result.output


def test_pyname_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            restore_settings()
            result = runner.invoke(hatch, ['shed', '-p', 'pyname'])

        assert result.exit_code == 0
        assert 'Python path named `pyname` already does not exist.' in result.output


def test_env():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        venv_dir = os.path.join(VENV_DIR, env_name)

        try:
            runner.invoke(hatch, ['env', env_name])
            assert os.path.exists(venv_dir)
            result = runner.invoke(hatch, ['shed', '-e', env_name])
            assert not os.path.exists(venv_dir)
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
        assert 'Successfully removed virtual env named `{}`.'.format(env_name) in result.output


def test_env_not_exist():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        result = runner.invoke(hatch, ['shed', '-e', env_name])

        assert result.exit_code == 0
        assert 'Virtual env named `{}` already does not exist.'.format(env_name)
