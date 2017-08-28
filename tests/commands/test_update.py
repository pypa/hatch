import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import install_packages
from hatch.utils import remove_path, temp_chdir
from hatch.venv import VENV_DIR, create_venv, venv
from ..utils import get_version_as_bytes


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
            result = runner.invoke(hatch, ['update'])
            final_version = get_version_as_bytes('requests')

        assert result.exit_code == 0
        assert initial_version < final_version
        assert 'Successfully updated.' in result.output


def test_requirements_none():
    with temp_chdir() as d:
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            runner = CliRunner()
            result = runner.invoke(hatch, ['update'])

        assert result.exit_code == 1
        assert 'Unable to locate a requirements file.' in result.output


def test_packages():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['requests==2.17.3', 'six==1.9.0'])
            initial_version_requests = get_version_as_bytes('requests')
            initial_version_six = get_version_as_bytes('six')
            result = runner.invoke(hatch, ['update', 'six'])
            final_version_requests = get_version_as_bytes('requests')
            final_version_six = get_version_as_bytes('six')

        assert result.exit_code == 0
        assert initial_version_requests == final_version_requests
        assert initial_version_six < final_version_six
        assert 'Successfully updated.' in result.output


def test_all_packages():
    with temp_chdir() as d:
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['requests==2.17.3'])
            initial_version = get_version_as_bytes('requests')
            runner = CliRunner()
            result = runner.invoke(hatch, ['update', '--all'])
            final_version = get_version_as_bytes('requests')

        assert result.exit_code == 0
        assert initial_version < final_version
        assert 'Successfully updated.' in result.output


def test_all_packages_none():
    with temp_chdir() as d:
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            runner = CliRunner()
            result = runner.invoke(hatch, ['update', '--all'])

        assert result.exit_code == 1
        assert 'No packages installed.' in result.output


def test_env_not_exist():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        result = runner.invoke(hatch, ['update', '-e', env_name])

        assert result.exit_code == 1
        assert 'Virtual env named `{}` already does not exist.'.format(env_name)


def test_env():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

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
        assert 'Successfully updated virtual env named `{}`.'.format(env_name) in result.output


def test_infra():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['setuptools==36.0.1'])
            initial_version = get_version_as_bytes('setuptools')
            result = runner.invoke(hatch, ['update', '--infra'])
            final_version = get_version_as_bytes('setuptools')

        assert result.exit_code == 0
        assert initial_version < final_version
        assert 'Successfully updated.' in result.output


def test_infra_env():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

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
        assert 'Successfully updated virtual env named `{}`.'.format(env_name) in result.output
