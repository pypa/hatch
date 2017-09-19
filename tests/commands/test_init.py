import os
import sys

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import get_editable_packages, get_python_version
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, restore_settings, save_settings
)
from hatch.utils import create_file, remove_path, temp_chdir, temp_move_path
from hatch.venv import VENV_DIR, create_venv, get_new_venv_name, venv
from ..utils import matching_file, wait_for_os


def test_config_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])

        assert result.exit_code == 1
        assert 'Unable to locate config file. Try `hatch config --restore`.' in result.output


def test_invalid_name():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'invalid-name', '--basic', '-ne'])

        assert os.path.exists(os.path.join(d, 'invalid_name', '__init__.py'))


def test_output():
    with temp_chdir():
        runner = CliRunner()
        result = runner.invoke(hatch, ['init', 'new-project', '--basic', '-ne'])

        assert result.exit_code == 0
        assert 'Created project `new-project` here' in result.output


def test_env():
    with temp_chdir() as d:
        runner = CliRunner()
        result = runner.invoke(hatch, ['init', 'new-project', '--basic'])
        wait_for_os()

        with venv(os.path.join(d, 'venv')):
            assert 'new-project' in get_editable_packages()

        assert result.exit_code == 0
        assert 'Creating its own virtual env... complete!' in result.output
        assert 'Installing locally in the virtual env... complete!' in result.output


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
                result = runner.invoke(hatch, ['init', 'ok', '-py', 'python'])
                venv_dir = os.path.join(d, 'venv')
                global_version = get_python_version()
                wait_for_os()
                with venv(venv_dir):
                    assert get_python_version() == global_version
        finally:
            remove_path(venv_dir)

        assert result.exit_code == 0


def test_pyname_config_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['init', 'ok', '-py', 'python'])

        assert result.exit_code == 1
        assert 'Unable to locate config file. Try `hatch config --restore`.' in result.output


def test_pyname_key_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            restore_settings()
            result = runner.invoke(hatch, ['init', 'ok', '-py', 'pyname'])

        assert result.exit_code == 1
        assert 'Unable to find a Python path named `pyname`.' in result.output


def test_basic():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])

        assert os.path.exists(os.path.join(d, 'ok', '__init__.py'))
        assert os.path.exists(os.path.join(d, 'tests', '__init__.py'))
        assert os.path.exists(os.path.join(d, 'setup.py'))
        assert os.path.exists(os.path.join(d, 'MANIFEST.in'))
        assert os.path.exists(os.path.join(d, 'requirements.txt'))
        assert os.path.exists(os.path.join(d, '.coveragerc'))
        assert os.path.exists(os.path.join(d, 'tox.ini'))
        assert matching_file(r'^LICENSE.*', os.listdir(d))
        assert matching_file(r'^README.*', os.listdir(d))


def test_cli():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--cli', '-ne'])

        assert os.path.exists(os.path.join(d, 'ok', 'cli.py'))
        assert os.path.exists(os.path.join(d, 'ok', '__main__.py'))


def test_license_single():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-l', 'cc0', '-ne'])

        assert os.path.exists(os.path.join(d, 'LICENSE-CC0'))


def test_license_multiple():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-l', 'cc0,mpl', '-ne'])

        assert os.path.exists(os.path.join(d, 'LICENSE-CC0'))
        assert os.path.exists(os.path.join(d, 'LICENSE-MPL'))


def test_extras():
    with temp_chdir() as d:
        runner = CliRunner()
        test_dir = os.path.join(d, 'a', 'b')
        test_file1 = os.path.join(test_dir, 'file1.txt')
        test_file2 = os.path.join(d, 'x', 'y', 'file2.txt')
        test_glob = '{}{}*'.format(os.path.join(d, 'x'), os.path.sep)
        fake_file = os.path.join(test_dir, 'file.py')
        create_file(test_file1)
        create_file(test_file2)

        with temp_move_path(SETTINGS_FILE, d):
            new_settings = copy_default_settings()
            new_settings['extras'] = [test_dir, test_file1, test_glob, fake_file]
            save_settings(new_settings)

            runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])

        assert os.path.exists(os.path.join(d, 'b', 'file1.txt'))
        assert os.path.exists(os.path.join(d, 'file1.txt'))
        assert os.path.exists(os.path.join(d, 'y', 'file2.txt'))
        assert not os.path.exists(os.path.join(d, 'file2.txt'))
        assert not os.path.exists(os.path.join(d, 'file.py'))


def test_envs():
    with temp_chdir():
        runner = CliRunner()
        env_name1, env_name2 = get_new_venv_name(count=2)
        venv_dir1 = os.path.join(VENV_DIR, env_name1)
        venv_dir2 = os.path.join(VENV_DIR, env_name2)
        create_venv(venv_dir1)

        try:
            result = runner.invoke(hatch, [
                'init', '-ne', '--basic', 'ok', '-e', '{}/{}'.format(env_name1, env_name2)
            ])
            wait_for_os()
            with venv(venv_dir1):
                assert 'ok' in get_editable_packages()
            with venv(venv_dir2):
                assert 'ok' in get_editable_packages()
        finally:
            remove_path(venv_dir1)
            remove_path(venv_dir2)

        assert result.exit_code == 0
        assert 'Creating virtual env `{}`... complete!'.format(env_name1) not in result.output
        assert 'Creating virtual env `{}`... complete!'.format(env_name2) in result.output
        assert 'Installing locally in virtual env `{}`... complete!'.format(env_name1) in result.output
        assert 'Installing locally in virtual env `{}`... complete!'.format(env_name2) in result.output
