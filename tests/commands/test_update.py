import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import (
    get_installed_packages, get_python_implementation, install_packages
)
from hatch.utils import remove_path, temp_chdir
from hatch.venv import VENV_DIR, create_venv, get_new_venv_name, is_venv, venv
from ..utils import get_version_as_bytes
from ..utils import requires_internet, wait_for_os, wait_until


@requires_internet
def test_project_no_venv():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-ne'])
        venv_dir = os.path.join(d, 'venv')

        assert not os.path.exists(venv_dir)
        result = runner.invoke(hatch, ['update', 'six'])
        wait_until(is_venv, venv_dir)
        assert os.path.exists(venv_dir)

        with venv(venv_dir):
            assert 'ok' in get_installed_packages()

        assert result.exit_code == 0
        assert 'A project has been detected!' in result.output
        assert 'Creating a dedicated virtual env... complete!' in result.output
        assert 'Installing this project in the virtual env... complete!' in result.output
        assert 'Updating for this project...' in result.output


@requires_internet
def test_project_existing_venv():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok'])
        venv_dir = os.path.join(d, 'venv')
        wait_until(is_venv, venv_dir)
        assert os.path.exists(venv_dir)

        runner.invoke(hatch, ['install', 'six==1.9.0'])
        wait_for_os()

        with venv(venv_dir):
            assert 'ok' in get_installed_packages()
            initial_version = get_version_as_bytes('six')

        result = runner.invoke(hatch, ['update', 'six'])
        wait_for_os()

        with venv(venv_dir):
            final_version = get_version_as_bytes('six')

        assert result.exit_code == 0
        assert initial_version < final_version
        assert 'A project has been detected!' not in result.output
        assert 'Updating for this project...' in result.output


@requires_internet
def test_project_existing_venv_all_packages():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok'])
        venv_dir = os.path.join(d, 'venv')
        wait_until(is_venv, venv_dir)
        assert os.path.exists(venv_dir)

        runner.invoke(hatch, ['install', 'six==1.9.0'])
        wait_for_os()
        assert os.path.exists(venv_dir)

        with venv(venv_dir):
            assert 'ok' in get_installed_packages()
            initial_version = get_version_as_bytes('six')

        result = runner.invoke(hatch, ['update', '--all'])
        wait_for_os()

        with venv(venv_dir):
            final_version = get_version_as_bytes('six')

        assert result.exit_code == 0
        assert initial_version < final_version
        assert 'A project has been detected!' not in result.output
        assert 'Updating for this project...' in result.output


@requires_internet
def test_requirements():
    with temp_chdir() as d:
        with open(os.path.join(d, 'requirements.txt'), 'w') as f:
            f.write('requests==2.18.1\n')

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['requests==2.17.3'])
            initial_version = get_version_as_bytes('requests')
            runner = CliRunner()
            result = runner.invoke(hatch, ['update', '-nd'])
            final_version = get_version_as_bytes('requests')

        assert result.exit_code == 0
        assert initial_version < final_version


@requires_internet
def test_dev_requirements():
    with temp_chdir() as d:
        with open(os.path.join(d, 'dev-requirements.txt'), 'w') as f:
            f.write('requests==2.18.1\n')

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['requests==2.17.3'])
            initial_version = get_version_as_bytes('requests')
            runner = CliRunner()
            result = runner.invoke(hatch, ['update', '-nd'])
            final_version = get_version_as_bytes('requests')

        assert result.exit_code == 0
        assert initial_version < final_version


@requires_internet
def test_requirements_dev():
    with temp_chdir() as d:
        with open(os.path.join(d, 'requirements-dev.txt'), 'w') as f:
            f.write('requests==2.18.1\n')

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['requests==2.17.3'])
            initial_version = get_version_as_bytes('requests')
            runner = CliRunner()
            result = runner.invoke(hatch, ['update', '-nd'])
            final_version = get_version_as_bytes('requests')

        assert result.exit_code == 0
        assert initial_version < final_version


@requires_internet
def test_requirements_includes_hatch():
    with temp_chdir() as d:
        runner = CliRunner()
        with open(os.path.join(d, 'requirements.txt'), 'w') as f:
            f.write('requests==2.18.1\nhatch>=0.0.1\n')

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['requests==2.17.3'])
            initial_version = get_version_as_bytes('requests')
            result = runner.invoke(hatch, ['update', '-nd'])
            final_version = get_version_as_bytes('requests')
            installed_packages = get_installed_packages()

        assert result.exit_code == 0
        assert initial_version < final_version
        assert 'hatch' not in installed_packages


def test_requirements_none():
    with temp_chdir() as d:
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            runner = CliRunner()
            result = runner.invoke(hatch, ['update', '-nd'])

        assert result.exit_code == 1
        assert 'Unable to locate a requirements file.' in result.output


@requires_internet
def test_packages():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['requests==2.17.3', 'six==1.9.0'])
            initial_version_requests = get_version_as_bytes('requests')
            initial_version_six = get_version_as_bytes('six')
            result = runner.invoke(hatch, ['update', '-nd', 'six'])
            final_version_requests = get_version_as_bytes('requests')
            final_version_six = get_version_as_bytes('six')

        assert result.exit_code == 0
        assert initial_version_requests == final_version_requests
        assert initial_version_six < final_version_six


def test_packages_only_hatch():
    with temp_chdir():
        runner = CliRunner()
        result = runner.invoke(hatch, ['update', '-nd', 'hatch'])

        assert result.exit_code == 1
        assert 'No packages to install.' in result.output


@requires_internet
def test_all_packages():
    with temp_chdir() as d:
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['requests==2.17.3'])
            initial_version = get_version_as_bytes('requests')
            runner = CliRunner()
            result = runner.invoke(hatch, ['update', '-nd', '--all'])
            final_version = get_version_as_bytes('requests')

        assert result.exit_code == 0
        assert initial_version < final_version


def test_all_packages_none():
    with temp_chdir() as d:
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            runner = CliRunner()
            result = runner.invoke(hatch, ['update', '-nd', '--all'])

        if get_python_implementation() in {'PyPy'}:  # no cov
            assert result.exit_code == 0
        else:
            assert result.exit_code == 1
            assert 'No packages installed.' in result.output


def test_env_not_exist():
    with temp_chdir():
        runner = CliRunner()

        env_name = get_new_venv_name()
        result = runner.invoke(hatch, ['update', '-e', env_name])

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
            with venv(venv_dir):
                install_packages(['requests==2.17.3'])
                initial_version = get_version_as_bytes('requests')
            result = runner.invoke(hatch, ['update', '-e', env_name, '--all'])
            with venv(venv_dir):
                final_version = get_version_as_bytes('requests')
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
        assert initial_version < final_version


@requires_internet
def test_infra():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['setuptools==36.0.1'])
            initial_version = get_version_as_bytes('setuptools')
            result = runner.invoke(hatch, ['update', '-nd', '--infra'])
            final_version = get_version_as_bytes('setuptools')

        assert result.exit_code == 0
        assert initial_version < final_version


@requires_internet
def test_infra_env():
    with temp_chdir():
        runner = CliRunner()

        env_name = get_new_venv_name()
        venv_dir = os.path.join(VENV_DIR, env_name)
        create_venv(venv_dir)

        try:
            with venv(venv_dir):
                install_packages(['setuptools==36.0.1'])
                initial_version = get_version_as_bytes('setuptools')
            result = runner.invoke(hatch, ['update', '-e', env_name, '--infra'])
            with venv(venv_dir):
                final_version = get_version_as_bytes('setuptools')
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
        assert initial_version < final_version
