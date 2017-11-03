import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.config import get_venv_dir
from hatch.env import get_editable_packages, get_installed_packages
from hatch.utils import env_vars, remove_path, temp_chdir
from hatch.venv import create_venv, get_new_venv_name, is_venv, venv
from hatch.project import Project
from ..utils import requires_internet, wait_for_os, wait_until


def test_project_no_venv():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-ne'])
        runner.invoke(hatch, ['new', 'ko', '-ne'])
        venv_dir = os.path.join(d, 'venv')
        package_dir = os.path.join(d, 'ko')

        assert not os.path.exists(venv_dir)
        with env_vars({'_IGNORE_VENV_': '1'}):
            result = runner.invoke(hatch, ['install', package_dir])
        wait_until(is_venv, venv_dir)
        assert os.path.exists(venv_dir)

        with venv(venv_dir):
            assert 'ok' in get_editable_packages()
            assert 'ko' in get_installed_packages(editable=False)

        assert result.exit_code == 0
        assert 'A project has been detected!' in result.output
        assert 'Creating a dedicated virtual env... complete!' in result.output
        assert 'Installing this project in the virtual env... complete!' in result.output
        assert 'Installing for this project...' in result.output


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
            result = runner.invoke(hatch, ['install', package_dir])
        wait_for_os()

        with venv(venv_dir):
            assert 'ok' in get_editable_packages()
            assert 'ko' in get_installed_packages(editable=False)

        assert result.exit_code == 0
        assert 'A project has been detected!' not in result.output
        assert 'Installing for this project...' in result.output

@requires_internet
def test_project_file_adds_dependency():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok'])
        venv_dir = os.path.join(d, 'venv')
        wait_until(is_venv, venv_dir)
        assert os.path.exists(venv_dir)

        project_file = os.path.join(d, 'pyproject.toml')
        assert os.path.exists(project_file)
        project = Project(project_file)
        assert project.packages == {}
        assert project.dev_packages == {}

        result = runner.invoke(hatch, ['install', 'six'])
        wait_for_os()
        assert result.exit_code == 0

        with venv(venv_dir):
            assert 'six' in get_installed_packages(editable=False)

        result = runner.invoke(hatch, ['install', '--dev', 'fuzzyfinder'])
        wait_for_os()
        assert result.exit_code == 0

        project = Project(project_file)
        with venv(venv_dir):
            assert 'six' in project.packages
            assert 'fuzzyfinder' in project.dev_packages

        setup_file = os.path.join(d, 'setup.py')
        assert os.path.exists(setup_file)
        setup = open(setup_file).read()
        assert "REQUIRES = ['six']\n" in setup

def test_empty_install_installs_dependencies():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok'])
        venv_dir = os.path.join(d, 'venv')
        wait_until(is_venv, venv_dir)
        assert os.path.exists(venv_dir)

        project_file = os.path.join(d, 'pyproject.toml')
        assert os.path.exists(project_file)
        project = Project(project_file)
        project.add_package('six', '1.11.0')

        result = runner.invoke(hatch, ['install'])
        wait_for_os()
        assert result.exit_code == 0
        with venv(venv_dir):
            assert 'six' in get_installed_packages(editable=False)
            assert 'ok' in get_editable_packages()


def test_non_existent_project_file_installs_current_package():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok'])
        venv_dir = os.path.join(d, 'venv')
        wait_until(is_venv, venv_dir)
        assert os.path.exists(venv_dir)

        project_file = os.path.join(d, 'pyproject.toml')
        os.remove(project_file)

        result = runner.invoke(hatch, ['install'])
        wait_for_os()
        assert result.exit_code == 0
        with venv(venv_dir):
            assert 'ok' in get_editable_packages()


def test_local():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-ne'])

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            assert 'ok' not in get_installed_packages()
            result = runner.invoke(hatch, ['install', '-nd'])
            assert 'ok' in get_installed_packages()

        assert result.exit_code == 0


def test_local_editable():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-ne'])

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            assert 'ok' not in get_editable_packages()
            result = runner.invoke(hatch, ['install', '-nd', '-l'])
            assert 'ok' in get_editable_packages()

        assert result.exit_code == 0


def test_local_none():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['install', '-nd'])

        assert result.exit_code != 0


@requires_internet
def test_packages():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            assert 'six' not in get_installed_packages()
            result = runner.invoke(hatch, ['install', '-nd', 'six'])
            assert 'six' in get_installed_packages()

        assert result.exit_code == 0


def test_env_not_exist():
    with temp_chdir():
        runner = CliRunner()

        env_name = get_new_venv_name()
        result = runner.invoke(hatch, ['install', '-e', env_name])

        assert result.exit_code == 1
        assert 'Virtual env named `{}` does not exist.'.format(env_name) in result.output


@requires_internet
def test_env():
    with temp_chdir():
        runner = CliRunner()

        env_name = get_new_venv_name()
        venv_dir = os.path.join(get_venv_dir(), env_name)
        create_venv(venv_dir)

        try:
            with venv(venv_dir):
                assert 'six' not in get_installed_packages()
            result = runner.invoke(hatch, ['install', '-e', env_name, 'six'])
            with venv(venv_dir):
                assert 'six' in get_installed_packages()
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
