import os

from click.testing import CliRunner
from twine.utils import TEST_REPOSITORY

from hatch.cli import hatch
from hatch.env import install_packages
from hatch.settings import SETTINGS_FILE, copy_default_settings, save_settings
from hatch.utils import env_vars, temp_chdir, temp_move_path
from hatch.venv import create_venv, venv
from ..utils import requires_internet

PACKAGE_NAME = 'e00f69943529ccc38058'
USERNAME = 'Ofekmeister'
ENV_VARS = {'TWINE_PASSWORD': 'badpwbestpw'}


@requires_internet
def test_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build'])
        os.chdir(os.path.join(d, 'dist'))

        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-u', USERNAME, '-t'])

        assert result.exit_code == 0

@requires_internet
def test_username_env():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build'])
        os.chdir(os.path.join(d, 'dist'))

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['pypi_username'] = ''
            save_settings(settings)
            extra_env_vars = {'TWINE_USERNAME': USERNAME, **ENV_VARS}
            with env_vars(extra_env_vars):
                result = runner.invoke(hatch, ['release', '-t'])

        assert result.exit_code == 0

@requires_internet
def test_cwd_dist_exists():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build'])

        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-u', USERNAME, '-t'])

        assert result.exit_code == 0


@requires_internet
def test_package():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', PACKAGE_NAME, '--basic', '-ne'])
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


@requires_internet
def test_local():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build', '-p', PACKAGE_NAME])
        package_dir = os.path.join(d, PACKAGE_NAME)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir, evars=ENV_VARS):
            install_packages(['-e', package_dir])
            result = runner.invoke(hatch, ['release', '-l', '-u', USERNAME, '-t'])

        assert result.exit_code == 0


def test_local_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['release', '-l'])

        assert result.exit_code == 1
        assert 'There are no local packages available.' in result.output


def test_local_multiple():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])
        runner.invoke(hatch, ['new', 'ko', '--basic', '-ne'])

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['-e', os.path.join(d, 'ok')])
            install_packages(['-e', os.path.join(d, 'ko')])

            result = runner.invoke(hatch, ['release', '-l'])

        assert result.exit_code == 1
        assert (
            'There are multiple local packages available. '
            'Select one with the optional argument.'
        ) in result.output


@requires_internet
def test_path_relative():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build'])

        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-p', 'dist', '-u', USERNAME, '-t'])

        print(result.output)
        assert result.exit_code == 0


@requires_internet
def test_path_full():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['new', 'ko', '--basic', '-ne'])
        runner.invoke(hatch, ['build', '-p', PACKAGE_NAME])
        build_dir = os.path.join(d, PACKAGE_NAME, 'dist')

        os.chdir(os.path.join(d, 'ko'))
        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-p', build_dir, '-u', USERNAME, '-t'])

        assert result.exit_code == 0


def test_path_full_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', PACKAGE_NAME, '--basic', '-ne'])

        full_path = os.path.join(d, 'dist')
        result = runner.invoke(hatch, ['release', '-p', full_path])

        assert result.exit_code == 1
        assert 'Directory `{}` does not exist.'.format(full_path) in result.output


@requires_internet
def test_config_username():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic', '-ne'])
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
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build'])

        with temp_move_path(SETTINGS_FILE, d):
            with env_vars(ENV_VARS):
                result = runner.invoke(hatch, ['release', '-p', 'dist', '-t'])

        assert result.exit_code == 1
        assert 'Unable to locate config file. Try `hatch config --restore`.' in result.output


def test_config_username_empty():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build'])

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['pypi_username'] = ''
            save_settings(settings)
            with env_vars(ENV_VARS):
                result = runner.invoke(hatch, ['release', '-p', 'dist', '-t'])

        assert result.exit_code == 1
        assert (
            'A username must be supplied via -u/--username, '
            'in {} as pypi_username, or in the TWINE_USERNAME environment variable.'.format(SETTINGS_FILE)
        ) in result.output


def test_strict():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build'])

        with env_vars(ENV_VARS):
            result = runner.invoke(hatch, ['release', '-p', 'dist', '-u', USERNAME, '-t', '-s'])

        assert result.exit_code == 1


def test_repository_local():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build', '-p', PACKAGE_NAME])
        package_dir = os.path.join(d, PACKAGE_NAME)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        # Make sure there's no configuration
        with temp_move_path(os.path.expanduser("~/.pypirc"), d):
            with venv(venv_dir, evars=ENV_VARS):
                install_packages(['-e', package_dir])
                # Will error, since there's no configuration parameter for
                # this URL
                result = runner.invoke(hatch, ['release', '-l', '-u', USERNAME, '-r', TEST_REPOSITORY])

        assert result.exit_code == 1


@requires_internet
def test_repository_url_local():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build', '-p', PACKAGE_NAME])
        package_dir = os.path.join(d, PACKAGE_NAME)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir, evars=ENV_VARS):
            install_packages(['-e', package_dir])
            result = runner.invoke(hatch, ['release', '-l', '-u', USERNAME,
                                           '--repository-url', TEST_REPOSITORY])

        assert result.exit_code == 0


@requires_internet
def test_repository_and_repository_url_local():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build', '-p', PACKAGE_NAME])
        package_dir = os.path.join(d, PACKAGE_NAME)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir, evars=ENV_VARS):
            install_packages(['-e', package_dir])
            result = runner.invoke(hatch, ['release', '-l', '-u', USERNAME,
                                           '--repository', TEST_REPOSITORY,
                                           '--repository-url', TEST_REPOSITORY])

        assert result.exit_code == 0

@requires_internet
def test_repository_env_vars():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build', '-p', PACKAGE_NAME])
        package_dir = os.path.join(d, PACKAGE_NAME)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        extra_env_vars = {'TWINE_REPOSITORY': TEST_REPOSITORY, 'TWINE_REPOSITORY_URL': TEST_REPOSITORY, **ENV_VARS}
        with venv(venv_dir, evars=extra_env_vars):
            install_packages(['-e', package_dir])
            result = runner.invoke(hatch, ['release', '-l', '-u', USERNAME])

        assert result.exit_code == 0


def test_repository_and_test():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', PACKAGE_NAME, '--basic', '-ne'])
        runner.invoke(hatch, ['build', '-p', PACKAGE_NAME])
        package_dir = os.path.join(d, PACKAGE_NAME)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir, evars=ENV_VARS):
            install_packages(['-e', package_dir])
            result = runner.invoke(hatch, ['release', '-l', '-u', USERNAME,
                                           '-r', TEST_REPOSITORY,
                                           '-t'])

        assert result.exit_code == 1
        assert "Cannot specify both --test and --repository." in result.output

        with venv(venv_dir, evars=ENV_VARS):
            result = runner.invoke(hatch, ['release', '-l', '-u', USERNAME,
                                           '--repository-url', TEST_REPOSITORY,
                                           '-t'])

        assert result.exit_code == 1
        assert "Cannot specify both --test and --repository-url." in result.output

        with venv(venv_dir, evars=ENV_VARS):
            result = runner.invoke(hatch, ['release', '-l', '-u', USERNAME,
                                           '-r', TEST_REPOSITORY,
                                           '--repository-url', TEST_REPOSITORY,
                                           '-t'])

        assert result.exit_code == 1
        assert "Cannot specify both --test and --repository." in result.output
        assert "Cannot specify both --test and --repository-url." in result.output
