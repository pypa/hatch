import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import get_installed_packages
from hatch.utils import env_vars, remove_path, temp_chdir
from hatch.venv import VENV_DIR, create_venv, get_new_venv_name, is_venv, venv
from ..utils import requires_internet, wait_for_os, wait_until


def test_project_no_venv():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-ne'])
        venv_dir = os.path.join(d, 'venv')

        assert not os.path.exists(venv_dir)
        with env_vars({'_IGNORE_VENV_': '1'}):
            result = runner.invoke(hatch, ['uninstall', 'ko', '-y'])
        wait_until(is_venv, venv_dir)
        assert os.path.exists(venv_dir)

        assert result.exit_code == 2
        assert 'A project has been detected!' in result.output
        assert 'Creating a dedicated virtual env... complete!' in result.output
        assert 'Installing this project in the virtual env... complete!' in result.output
        assert 'New virtual envs have nothing to uninstall, exiting...' in result.output
        assert 'Uninstalling for this project...' not in result.output


def test_project_existing_venv():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok'])
        runner.invoke(hatch, ['new', 'ko', '-ne'])
        venv_dir = os.path.join(d, 'venv')
        package_dir = os.path.join(d, 'ko')
        wait_until(is_venv, venv_dir)
        assert os.path.exists(venv_dir)

        with env_vars({'_IGNORE_VENV_': '1'}):
            runner.invoke(hatch, ['install', package_dir])
        wait_for_os()

        with venv(venv_dir):
            assert 'ko' in get_installed_packages(editable=False)

        with env_vars({'_IGNORE_VENV_': '1'}):
            result = runner.invoke(hatch, ['uninstall', 'ko', '-y'])
        wait_for_os()

        with venv(venv_dir):
            assert 'ko' not in get_installed_packages(editable=False)

        assert result.exit_code == 0
        assert 'A project has been detected!' not in result.output
        assert 'Uninstalling for this project...' in result.output


def test_project_not_detected_when_venv_active():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-ne'])
        runner.invoke(hatch, ['new', 'ko'])
        venv_dir = os.path.join(d, 'ko', 'venv')
        wait_until(is_venv, venv_dir)
        assert os.path.exists(venv_dir)

        with venv(venv_dir):
            runner.invoke(hatch, ['install'])
            wait_for_os()
            assert 'ok' in get_installed_packages(editable=False)
            result = runner.invoke(hatch, ['uninstall', 'ok', '-y'])
            wait_for_os()
            assert 'ok' not in get_installed_packages(editable=False)

        assert result.exit_code == 0
        assert 'A project has been detected!' not in result.output
        assert 'Uninstalling...' in result.output


@requires_internet
def test_requirements():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)
        with open(os.path.join(d, 'requirements.txt'), 'w') as f:
            f.write('six\n')

        with venv(venv_dir):
            runner.invoke(hatch, ['install', '-nd', 'six'])
            assert 'six' in get_installed_packages()
            result = runner.invoke(hatch, ['uninstall', '-nd', '-y'])
            assert 'six' not in get_installed_packages()

        assert result.exit_code == 0


def test_requirements_none():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['uninstall', '-nd', '-y'])

        assert result.exit_code == 1
        assert 'Unable to locate a requirements file.' in result.output


@requires_internet
def test_packages():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            runner.invoke(hatch, ['install', '-nd', 'six'])
            assert 'six' in get_installed_packages()
            result = runner.invoke(hatch, ['uninstall', '-nd', '-y', 'six'])
            assert 'six' not in get_installed_packages()

        assert result.exit_code == 0


def test_env_not_exist():
    with temp_chdir():
        runner = CliRunner()

        env_name = get_new_venv_name()
        result = runner.invoke(hatch, ['uninstall', '-nd', '-y', '-e', env_name, 'six'])

        assert result.exit_code == 1
        assert 'Virtual env named `{}` does not exist.'.format(env_name) in result.output


@requires_internet
def test_env():
    with temp_chdir():
        runner = CliRunner()

        env_name = get_new_venv_name()
        venv_dir = os.path.join(VENV_DIR, env_name)
        create_venv(venv_dir)

        try:
            runner.invoke(hatch, ['install', '-e', env_name, 'six'])
            with venv(venv_dir):
                assert 'six' in get_installed_packages()
            result = runner.invoke(hatch, ['uninstall', '-nd', '-y', '-e', env_name, 'six'])
            with venv(venv_dir):
                assert 'six' not in get_installed_packages()
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
