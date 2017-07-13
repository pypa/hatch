import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import install_packages
from hatch.utils import create_file, temp_chdir
from hatch.venv import create_venv, venv


def find_all_files(d):
    return [
        os.path.join(root, file)
        for root, dirs, files in os.walk(d)
        for file in files
    ]


def assert_files_exist(files):
    for file in files:
        assert os.path.exists(file)


def test_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        files = find_all_files(d)

        test_file = os.path.join(d, 'test.pyc')
        create_file(test_file)
        assert os.path.exists(test_file)

        result = runner.invoke(hatch, ['clean'])

        assert result.exit_code == 0
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_package():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])
        package_dir = os.path.join(d, 'ok')
        files = find_all_files(package_dir)

        test_file = os.path.join(package_dir, 'test.pyc')
        create_file(test_file)
        assert os.path.exists(test_file)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            os.chdir(package_dir)
            install_packages(['-e', '.'])
            os.chdir(d)

            result = runner.invoke(hatch, ['clean', 'ok'])

        assert result.exit_code == 0
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_package_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['clean', 'ok'])

        assert result.exit_code == 1
        assert '`{}` is not an editable package.'.format('ok') in result.output


def test_path_relative():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])
        package_dir = os.path.join(d, 'ok')
        files = find_all_files(package_dir)

        test_file = os.path.join(package_dir, 'test.pyc')
        create_file(test_file)
        assert os.path.exists(test_file)

        result = runner.invoke(hatch, ['clean', '-p', 'ok'])

        assert result.exit_code == 0
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_path_full():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])
        runner.invoke(hatch, ['egg', 'ko', '--basic'])
        package_dir = os.path.join(d, 'ok')
        files = find_all_files(package_dir)

        test_file = os.path.join(package_dir, 'test.pyc')
        create_file(test_file)
        assert os.path.exists(test_file)

        os.chdir(os.path.join(d, 'ko'))
        result = runner.invoke(hatch, ['clean', '-p', package_dir])

        assert result.exit_code == 0
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_path_full_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])

        full_path = os.path.join(d, 'ko')
        result = runner.invoke(hatch, ['clean', '-p', full_path])

        assert result.exit_code == 1
        assert 'Directory `{}` does not exist.'.format(full_path) in result.output
