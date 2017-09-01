import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import get_editable_packages, get_installed_packages
from hatch.utils import remove_path, temp_chdir
from hatch.venv import VENV_DIR, create_venv, venv


def test_local():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok'])

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            assert 'ok' not in get_installed_packages()
            result = runner.invoke(hatch, ['install'])
            assert 'ok' in get_installed_packages()

        assert result.exit_code == 0


def test_local_editable():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok'])

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            assert 'ok' not in get_editable_packages()
            result = runner.invoke(hatch, ['install', '-l'])
            assert 'ok' in get_editable_packages()

        assert result.exit_code == 0


def test_local_none():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['install'])

        assert result.exit_code != 0


def test_packages():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            assert 'six' not in get_installed_packages()
            result = runner.invoke(hatch, ['install', 'six'])
            assert 'six' in get_installed_packages()

        assert result.exit_code == 0


def test_env_not_exist():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        result = runner.invoke(hatch, ['install', '-e', env_name])

        assert result.exit_code == 1
        assert 'Virtual env named `{}` does not exist.'.format(env_name) in result.output


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
                assert 'six' not in get_installed_packages()
            result = runner.invoke(hatch, ['install', '-e', env_name, 'six'])
            with venv(venv_dir):
                assert 'six' in get_installed_packages()
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
