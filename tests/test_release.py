import os
import time

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.create import create_package
from hatch.env import install_packages
from hatch.settings import SETTINGS_FILE
from hatch.utils import create_file, env_vars, temp_chdir, temp_move_path
from hatch.venv import create_venv, venv

PACKAGE_NAME = 'e00f69943529ccc38058'
USERNAME = 'Ofekmeister'
ENV_VARS = {'TWINE_PASSWORD': 'badpwbestpw'}


def test_cwd():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic'])
        runner.invoke(hatch, ['build'])

        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-u', USERNAME, '-t'])

        assert result.exit_code == 0


def test_cwd_no_build():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic'])

        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-u', USERNAME, '-t'])

        assert result.exit_code == 1
        assert 'Directory `{}` does not exist.'.format(os.path.join(d, 'dist'))


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
        runner.invoke(hatch, ['egg', PACKAGE_NAME, '--basic'])
        runner.invoke(hatch, ['build', '-p', PACKAGE_NAME])

        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', PACKAGE_NAME, '-u', USERNAME, '-t'])

        assert result.exit_code == 0














