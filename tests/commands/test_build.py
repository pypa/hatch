import glob
import os
import sys

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import install_packages
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, save_settings
)
from hatch.utils import create_file, temp_chdir, temp_move_path
from hatch.venv import create_venv, venv
from ..utils import matching_file


def format_files(d):
    return ''.join(
        '{}\n'.format(path)
        for path in sorted(os.listdir(d))
        if os.path.isfile(os.path.join(d, path))
    )


def test_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        build_dir = os.path.join(d, 'dist')

        result = runner.invoke(hatch, ['build'])
        files = os.listdir(build_dir)

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', files)
        assert len(files) == 2
        assert (
            'Files found in `{}`:\n\n'.format(build_dir) + format_files(build_dir)
        ) in result.output


def test_package():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])
        package_dir = os.path.join(d, 'ok')
        build_dir = os.path.join(package_dir, 'dist')

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            os.chdir(package_dir)
            install_packages(['-e', '.'])
            os.chdir(d)

            result = runner.invoke(hatch, ['build', 'ok'])
            files = os.listdir(build_dir)

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', files)
        assert len(files) == 2
        assert (
            'Files found in `{}`:\n\n'.format(build_dir) + format_files(build_dir)
        ) in result.output


def test_package_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['build', 'ok'])

        assert result.exit_code == 1
        assert '`{}` is not an editable package.'.format('ok') in result.output


def test_path_relative():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])
        build_dir = os.path.join(d, 'ok', 'dist')

        result = runner.invoke(hatch, ['build', '-p', 'ok'])
        files = os.listdir(build_dir)

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', files)
        assert len(files) == 2
        assert (
            'Files found in `{}`:\n\n'.format(build_dir) + format_files(build_dir)
        ) in result.output


def test_path_full():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])
        runner.invoke(hatch, ['new', 'ko', '--basic'])
        package_dir = os.path.join(d, 'ok')
        build_dir = os.path.join(package_dir, 'dist')

        os.chdir(os.path.join(d, 'ko'))
        result = runner.invoke(hatch, ['build', '-p', package_dir])
        files = os.listdir(build_dir)

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', files)
        assert len(files) == 2
        assert (
            'Files found in `{}`:\n\n'.format(build_dir) + format_files(build_dir)
        ) in result.output


def test_path_full_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])

        full_path = os.path.join(d, 'ko')
        result = runner.invoke(hatch, ['build', '-p', full_path])

        assert result.exit_code == 1
        assert 'Directory `{}` does not exist.'.format(full_path) in result.output


def test_default_non_universal():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['build'])
        file_name = glob.glob(os.path.join(d, 'dist', '*.whl'))[0]

        assert result.exit_code == 0
        assert 'py2' in file_name or 'py3' in file_name
        assert not ('py2' in file_name and 'py3' in file_name)


def test_universal():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['build', '-u'])
        file_name = glob.glob(os.path.join(d, 'dist', '*.whl'))[0]

        assert result.exit_code == 0
        assert 'py2' in file_name and 'py3' in file_name


def test_platform_name():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['build', '-n', 'linux_x86_64'])
        files = os.listdir(os.path.join(d, 'dist'))

        assert result.exit_code == 0
        assert matching_file(r'linux_x86_64\.whl$', files)
        assert len(files) == 2


def test_build_dir_relative():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        build_dir = os.path.join(d, '_build_dir')
        os.makedirs(os.path.join(build_dir, 'd'))

        result = runner.invoke(hatch, ['build', '-d', '_build_dir'])
        files = os.listdir(build_dir)

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', files)
        assert len(files) == 3
        assert (
            'Files found in `{}`:\n\n'.format(build_dir) + format_files(build_dir)
        ) in result.output


def test_build_dir_full():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        build_dir = os.path.join(d, '_build_dir')

        result = runner.invoke(hatch, ['build', '-d', build_dir])
        files = os.listdir(build_dir)

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', files)
        assert len(files) == 2
        assert (
            'Files found in `{}`:\n\n'.format(build_dir) + format_files(build_dir)
        ) in result.output


def test_build_dir_file():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        build_dir = os.path.join(d, '_build_dir')
        create_file(build_dir)

        result = runner.invoke(hatch, ['build', '-d', build_dir])

        assert result.exit_code == 1
        assert 'Files found in' not in result.output


def test_clean():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        old_artifact = os.path.join(d, 'dist', 'foo.whl')
        create_file(old_artifact)
        assert os.path.exists(old_artifact)

        result = runner.invoke(hatch, ['build', '-c'])
        files = os.listdir(os.path.join(d, 'dist'))

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', files)
        assert len(files) == 2
        assert not os.path.exists(old_artifact)


def test_fail():
    with temp_chdir():
        runner = CliRunner()
        result = runner.invoke(hatch, ['build'])

        assert result.exit_code != 0


def test_pypath():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['build', '-pp', sys.executable])
        files = os.listdir(os.path.join(d, 'dist'))

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', files)
        assert len(files) == 2


def test_python():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['pypaths']['python'] = sys.executable
            save_settings(settings)
            result = runner.invoke(hatch, ['build', '-py', 'python', '-pp', 'Delphi'])
            files = os.listdir(os.path.join(d, 'dist'))

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', files)
        assert len(files) == 2


def test_python_no_config():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['build', '-py', 'python'])

        assert result.exit_code == 1
        assert 'Unable to locate config file. Try `hatch config --restore`.' in result.output


def test_python_invalid():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['pypaths']['python'] = ''
            save_settings(settings)
            result = runner.invoke(hatch, ['build', '-py', 'python'])

        assert result.exit_code == 1
        assert 'Python path named `python` does not exist or is invalid.' in result.output
