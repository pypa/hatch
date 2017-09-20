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
from hatch.venv import VENV_DIR, create_venv, get_new_venv_name, is_venv, venv
from ..utils import requires_internet, wait_until


def test_success():
    with temp_chdir():
        runner = CliRunner()

        env_name = get_new_venv_name()
        venv_dir = os.path.join(VENV_DIR, env_name)

        try:
            result = runner.invoke(hatch, ['env', env_name])
            wait_until(is_venv, venv_dir)
            assert os.path.exists(venv_dir)
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
        assert 'Successfully saved virtual env `{}` to `{}`.'.format(env_name, venv_dir) in result.output


def test_pyname():
    with temp_chdir() as d:
        runner = CliRunner()

        env_name = get_new_venv_name()
        venv_dir = os.path.join(VENV_DIR, env_name)

        try:
            with temp_move_path(SETTINGS_FILE, d):
                settings = copy_default_settings()
                settings['pypaths']['python'] = sys.executable
                save_settings(settings)
                result = runner.invoke(hatch, ['env', env_name, '-py', 'python'])
                wait_until(is_venv, venv_dir)
                assert os.path.exists(venv_dir)
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
        assert 'Successfully saved virtual env `{}` to `{}`.'.format(env_name, venv_dir) in result.output


def test_pyname_config_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['env', 'name', '-py', 'python'])

        assert result.exit_code == 1
        assert 'Unable to locate config file. Try `hatch config --restore`.' in result.output


def test_pyname_key_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            restore_settings()
            result = runner.invoke(hatch, ['env', 'name', '-py', 'pyname'])

        assert result.exit_code == 1
        assert 'Unable to find a Python path named `pyname`.' in result.output


def test_existing_venv():
    with temp_chdir():
        runner = CliRunner()

        env_name = get_new_venv_name()
        venv_dir = os.path.join(VENV_DIR, env_name)

        try:
            runner.invoke(hatch, ['env', env_name])
            wait_until(is_venv, venv_dir)
            result = runner.invoke(hatch, ['env', env_name])
        finally:
            remove_path(venv_dir)

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


def test_list_success_1():
    with temp_chdir():
        runner = CliRunner()

        env_name1, env_name2 = get_new_venv_name(count=2)
        venv_dir1 = os.path.join(VENV_DIR, env_name1)
        venv_dir2 = os.path.join(VENV_DIR, env_name2)

        try:
            runner.invoke(hatch, ['env', env_name1])
            wait_until(is_venv, venv_dir1)
            os.makedirs(venv_dir2)
            result = runner.invoke(hatch, ['env', '-l'])
        finally:
            remove_path(venv_dir1)
            remove_path(venv_dir2)

        assert result.exit_code == 0
        assert (
            '{} ->\n'
            '  Version: {}'.format(
                env_name1, get_python_version()
            )
        ) in result.output


def test_list_success_2():
    with temp_chdir():
        runner = CliRunner()

        env_name = get_new_venv_name()
        venv_dir = os.path.join(VENV_DIR, env_name)

        try:
            runner.invoke(hatch, ['env', env_name])
            wait_until(is_venv, venv_dir)
            result = runner.invoke(hatch, ['env', '-ll'])
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0
        assert (
            '{} ->\n'
            '  Version: {}\n'
            '  Implementation: {}'.format(
                env_name, get_python_version(), get_python_implementation()
            )
        ) in result.output


def test_list_success_3():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-ne'])

        env_name = get_new_venv_name()
        venv_dir = os.path.join(VENV_DIR, env_name)

        try:
            runner.invoke(hatch, ['env', env_name])
            wait_until(is_venv, venv_dir)
            runner.invoke(hatch, ['install', '-l', '-e', env_name])
            result = runner.invoke(hatch, ['env', '-lll'])
        finally:
            remove_path(os.path.join(VENV_DIR, env_name))

        assert result.exit_code == 0
        assert (
            '{} ->\n'
            '  Version: {}\n'
            '  Implementation: {}\n'
            '  Local packages: {}'.format(
                env_name, get_python_version(), get_python_implementation(), 'ok'
            )
        ) in result.output


def test_clone_venv_not_exist():
    with temp_chdir():
        runner = CliRunner()

        env_name = get_new_venv_name()
        result = runner.invoke(hatch, ['env', env_name, '-c', env_name])

        assert result.exit_code == 1
        assert 'Virtual env `{name}` does not exist.'.format(name=env_name) in result.output


@requires_internet
def test_clone_success():
    with temp_chdir():
        runner = CliRunner()

        origin, clone = get_new_venv_name(count=2)
        origin_dir = os.path.join(VENV_DIR, origin)
        clone_dir = os.path.join(VENV_DIR, clone)

        try:
            runner.invoke(hatch, ['env', origin])
            wait_until(is_venv, origin_dir)
            with venv(origin_dir):
                install_packages(['requests'])

            result = runner.invoke(hatch, ['env', clone, '-c', origin])
            wait_until(is_venv, clone_dir)
            with venv(clone_dir):
                install_packages(['six'])
                installed_packages = get_installed_packages()
        finally:
            remove_path(origin_dir)
            remove_path(clone_dir)

        assert result.exit_code == 0
        assert 'Successfully cloned virtual env `{}` from `{}` to `{}`.'.format(
            clone, origin, clone_dir) in result.output
        assert 'requests' in installed_packages
        assert 'six' in installed_packages


@requires_internet
def test_restore_success():
    with temp_chdir() as d:
        runner = CliRunner()

        env_name, fake_name = get_new_venv_name(count=2)
        venv_origin = os.path.join(d, env_name)
        venv_dir = os.path.join(VENV_DIR, env_name)
        fake_venv = os.path.join(VENV_DIR, fake_name)

        create_venv(venv_origin)
        copy_path(venv_origin, VENV_DIR)
        os.makedirs(fake_venv)

        try:
            runner.invoke(hatch, ['env', env_name])
            wait_until(is_venv, venv_dir)

            result = runner.invoke(hatch, ['env', '-r'])
            with venv(venv_dir):
                install_packages(['six'])
                installed_packages = get_installed_packages()
        finally:
            remove_path(venv_dir)
            remove_path(fake_venv)

        assert result.exit_code == 0
        assert 'Successfully restored all available virtual envs.' in result.output
        assert 'six' in installed_packages
