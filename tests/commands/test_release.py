import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import install_packages
from hatch.settings import SETTINGS_FILE, copy_default_settings, save_settings
from hatch.utils import env_vars, temp_chdir, temp_move_path
from hatch.venv import create_venv, venv

PACKAGE_NAME = 'e00f69943529ccc38058'
USERNAME = 'Ofekmeister'
ENV_VARS = {'TWINE_PASSWORD': 'badpwbestpw'}


def test_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic'])
        runner.invoke(hatch, ['build'])
        os.chdir(os.path.join(d, 'dist'))

        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-u', USERNAME, '-t'])

        assert result.exit_code == 0


def test_package():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', PACKAGE_NAME, '--basic'])
        runner.invoke(hatch, ['build', '-p', PACKAGE_NAME])
        package_dir = os.path.join(d, PACKAGE_NAME)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir, evars=ENV_VARS):
            os.chdir(package_dir)
            install_packages(['-e', '.'])
            os.chdir(d)

            result = runner.invoke(hatch, ['release', PACKAGE_NAME, '-u', USERNAME, '-t'])

        assert result.exit_code == 0


def test_package_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir, evars=ENV_VARS):
            result = runner.invoke(hatch, ['release', PACKAGE_NAME, '-u', USERNAME, '-t'])

        assert result.exit_code == 1
        assert '`{}` is not an editable package.'.format(PACKAGE_NAME) in result.output


def test_path_relative():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic'])
        runner.invoke(hatch, ['build'])

        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-p', 'dist', '-u', USERNAME, '-t'])

        print(result.output)
        assert result.exit_code == 0


def test_path_full():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', PACKAGE_NAME, '--basic'])
        runner.invoke(hatch, ['egg', 'ko', '--basic'])
        runner.invoke(hatch, ['build', '-p', PACKAGE_NAME])
        build_dir = os.path.join(d, PACKAGE_NAME, 'dist')

        os.chdir(os.path.join(d, 'ko'))
        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-p', build_dir, '-u', USERNAME, '-t'])

        assert result.exit_code == 0


def test_path_full_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', PACKAGE_NAME, '--basic'])

        full_path = os.path.join(d, 'dist')
        result = runner.invoke(hatch, ['release', '-p', full_path])

        assert result.exit_code == 1
        assert 'Directory `{}` does not exist.'.format(full_path) in result.output


def test_config_username():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic'])
        runner.invoke(hatch, ['build'])

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['pypi_username'] = USERNAME
            save_settings(settings)
            with env_vars(ENV_VARS):
                result = runner.invoke(hatch, ['release', '-p', 'dist', '-t'])

        assert result.exit_code == 0


def test_config_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic'])
        runner.invoke(hatch, ['build'])

        with temp_move_path(SETTINGS_FILE, d):
            with env_vars(ENV_VARS):
                result = runner.invoke(hatch, ['release', '-p', 'dist', '-t'])

        assert result.exit_code == 1
        assert 'Unable to locate config file. Try `hatch config --restore`.' in result.output


def test_config_username_empty():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic'])
        runner.invoke(hatch, ['build'])

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['pypi_username'] = ''
            save_settings(settings)
            with env_vars(ENV_VARS):
                result = runner.invoke(hatch, ['release', '-p', 'dist', '-t'])

        assert result.exit_code == 1
        assert (
            'A username must be supplied via -u/--username or '
            'in {} as pypi_username.'.format(SETTINGS_FILE)
            ) in result.output


def test_strict():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic'])
        runner.invoke(hatch, ['build'])

        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-p', 'dist', '-u', USERNAME, '-t', '-s'])

        assert result.exit_code == 1
