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


def test_pyname_multiple():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['pythons']['pyname1'] = 'pypath1'
            settings['pythons']['pyname2'] = 'pypath2'
            save_settings(settings)
            result = runner.invoke(hatch, ['shed', '-p', 'pyname1,pyname2'])
            assert load_settings()['pythons'] == {}

        assert result.exit_code == 0
        assert 'Successfully removed Python path named `pyname1`.' in result.output
        assert 'Successfully removed Python path named `pyname2`.' in result.output


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


def test_env_multiple():
    with temp_chdir():
        runner = CliRunner()

        env_name1 = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name1)):  # no cov
            env_name1 = os.urandom(10).hex()

        venv_dir1 = os.path.join(VENV_DIR, env_name1)
        env_name2 = ''
        venv_dir2 = ''

        try:
            runner.invoke(hatch, ['env', env_name1])
            assert os.path.exists(venv_dir1)

            env_name2 = os.urandom(10).hex()
            while os.path.exists(os.path.join(VENV_DIR, env_name2)):  # no cov
                env_name2 = os.urandom(10).hex()
            venv_dir2 = os.path.join(VENV_DIR, env_name2)
            runner.invoke(hatch, ['env', env_name2])
            assert os.path.exists(venv_dir2)

            result = runner.invoke(hatch, ['shed', '-e', '{},{}'.format(env_name1, env_name2)])
            assert not os.path.exists(venv_dir1)
            assert not os.path.exists(venv_dir2)
        finally:
            remove_path(venv_dir1)
            remove_path(venv_dir2)

        assert result.exit_code == 0
        assert 'Successfully removed virtual env named `{}`.'.format(env_name1) in result.output
        assert 'Successfully removed virtual env named `{}`.'.format(env_name2) in result.output


def test_env_not_exist():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        result = runner.invoke(hatch, ['shed', '-e', env_name])

        assert result.exit_code == 0
        assert 'Virtual env named `{}` already does not exist.'.format(env_name)
