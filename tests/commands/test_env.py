import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.settings import SETTINGS_FILE, restore_settings
from hatch.utils import remove_path, temp_chdir, temp_move_path
from hatch.venv import VENV_DIR


def test_success():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        venv_dir = os.path.join(VENV_DIR, env_name)

        try:
            result = runner.invoke(hatch, ['env', env_name])
            assert venv_dir
        finally:
            remove_path(os.path.join(VENV_DIR, env_name))

        assert result.exit_code == 0
        assert 'Successfully saved virtual env `{}` to `{}`.'.format(env_name, venv_dir) in result.output


def test_pyname_config_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['env', 'name', '-p', 'python'])

        assert result.exit_code == 1
        assert 'Unable to locate config file. Try `hatch config --restore`.' in result.output


def test_pyname_key_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            restore_settings()
            result = runner.invoke(hatch, ['env', 'name', '-p', 'pyname'])

        assert result.exit_code == 1
        assert 'Unable to find a Python path named `pyname`.' in result.output


def test_existing_venv():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        try:
            runner.invoke(hatch, ['env', env_name])
            result = runner.invoke(hatch, ['env', env_name])
        finally:
            remove_path(os.path.join(VENV_DIR, env_name))

        assert result.exit_code == 1
        assert (
            'Virtual env `{name}` already exists. To remove '
            'it do `hatch shed -e {name}`.'.format(name=env_name)
        ) in result.output


def test_pypath_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        fake_path = os.path.join(d, 'python')

        result = runner.invoke(hatch, ['env', 'name', '--pypath', fake_path])

        assert result.exit_code == 1
        assert (
            'Python path `{}` does not exist. Be sure to use the absolute path '
            'e.g. `/usr/bin/python` instead of simply `python`.'.format(fake_path)
        ) in result.output
