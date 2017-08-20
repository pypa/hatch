import os
import sys

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import (
    get_installed_packages, get_python_implementation, get_python_version,
    install_packages
)
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, restore_settings, save_settings
)
from hatch.utils import copy_path, remove_path, temp_chdir, temp_move_path
from hatch.venv import VENV_DIR, create_venv, venv


def test_success():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        venv_dir = os.path.join(VENV_DIR, env_name)

        try:
            result = runner.invoke(hatch, ['env', env_name])
            assert os.path.exists(venv_dir)
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
        assert 'Successfully saved virtual env `{}` to `{}`.'.format(env_name, venv_dir) in result.output


def test_pyname():
    with temp_chdir() as d:
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        venv_dir = os.path.join(VENV_DIR, env_name)

        try:
            with temp_move_path(SETTINGS_FILE, d):
                settings = copy_default_settings()
                settings['pythons']['python'] = sys.executable
                save_settings(settings)
                result = runner.invoke(hatch, ['env', env_name, '-p', 'python'])
                assert os.path.exists(venv_dir)
        finally:
            remove_path(venv_dir)

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


def test_list_success():
    with temp_chdir():
        runner = CliRunner()

        env_name1 = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name1)):  # no cov
            env_name1 = os.urandom(10).hex()
        env_name2 = ''

        try:
            runner.invoke(hatch, ['env', env_name1])
            env_name2 = os.urandom(10).hex()
            while os.path.exists(os.path.join(VENV_DIR, env_name2)):  # no cov
                env_name2 = os.urandom(10).hex()
            os.makedirs(os.path.join(VENV_DIR, env_name2))
            result = runner.invoke(hatch, ['env', '-l'])
        finally:
            remove_path(os.path.join(VENV_DIR, env_name1))
            remove_path(os.path.join(VENV_DIR, env_name2))

        assert result.exit_code == 0
        assert (
            '{} ->\n'
            '  Version: {}\n'
            '  Implementation: {}'.format(
                env_name1, get_python_version(), get_python_implementation()
            )
        ) in result.output


def test_clone_venv_not_exist():
    with temp_chdir():
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        result = runner.invoke(hatch, ['env', env_name, '-c', env_name])

        assert result.exit_code == 1
        assert 'Virtual env `{name}` does not exist.'.format(name=env_name) in result.output


def test_clone_success():
    with temp_chdir():
        runner = CliRunner()

        origin = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, origin)):  # no cov
            origin = os.urandom(10).hex()

        origin_dir = os.path.join(VENV_DIR, origin)
        clone_dir = origin_dir

        try:
            runner.invoke(hatch, ['env', origin])
            with venv(origin_dir):
                install_packages(['requests'])

            clone = os.urandom(10).hex()
            while os.path.exists(os.path.join(VENV_DIR, clone)):  # no cov
                clone = os.urandom(10).hex()

            clone_dir = os.path.join(VENV_DIR, clone)

            result = runner.invoke(hatch, ['env', clone, '-c', origin])
            with venv(clone_dir):
                install_packages(['six'])
                installed_packages = get_installed_packages()
        finally:
            remove_path(origin_dir)
            remove_path(clone_dir)

        assert result.exit_code == 0
        assert 'Successfully cloned virtual env `{}` from `{}` to {}.'.format(
            clone, origin, clone_dir) in result.output
        assert 'requests' in installed_packages
        assert 'six' in installed_packages


def test_restore_success():
    with temp_chdir() as d:
        runner = CliRunner()

        env_name = os.urandom(10).hex()
        while os.path.exists(os.path.join(VENV_DIR, env_name)):  # no cov
            env_name = os.urandom(10).hex()

        venv_origin = os.path.join(d, env_name)
        create_venv(venv_origin)

        venv_dir = os.path.join(VENV_DIR, env_name)
        copy_path(venv_origin, VENV_DIR)

        try:
            runner.invoke(hatch, ['env', env_name])
            result = runner.invoke(hatch, ['env', '-r'])
            with venv(venv_dir):
                install_packages(['six'])
                installed_packages = get_installed_packages()
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
        assert 'Successfully restored all available virtual envs.' in result.output
        assert 'six' in installed_packages
