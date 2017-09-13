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

        test_file1 = os.path.join(d, 'test.pyc')
        test_file2 = os.path.join(d, 'ok.egg-info', 'entry_points.txt')
        create_file(test_file1)
        create_file(test_file2)
        assert os.path.exists(test_file1)
        assert os.path.exists(test_file2)

        result = runner.invoke(hatch, ['clean'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert not os.path.exists(test_file1)
        assert not os.path.exists(os.path.join(d, 'ok.egg-info'))
        assert_files_exist(files)


def test_cwd_compiled_only():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        files = find_all_files(d)

        test_file1 = os.path.join(d, 'test.pyc')
        test_file2 = os.path.join(d, 'ok', 'test.pyc')
        test_file3 = os.path.join(d, 'ok', 'deeper', 'test.pyc')
        create_file(test_file1)
        create_file(test_file2)
        create_file(test_file3)
        assert os.path.exists(test_file1)
        assert os.path.exists(test_file2)
        assert os.path.exists(test_file3)

        result = runner.invoke(hatch, ['clean', '-c'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert not os.path.exists(test_file1)
        assert not os.path.exists(test_file2)
        assert not os.path.exists(test_file3)
        assert_files_exist(files)


def test_package():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--cli'])
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
        assert 'Cleaned!' in result.output
        assert not os.path.exists(test_file)
        assert os.path.exists(os.path.join(package_dir, 'ok.egg-info'))
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
        runner.invoke(hatch, ['new', 'ok', '--basic'])
        package_dir = os.path.join(d, 'ok')
        files = find_all_files(package_dir)

        test_file = os.path.join(package_dir, 'test.pyc')
        create_file(test_file)
        assert os.path.exists(test_file)

        result = runner.invoke(hatch, ['clean', '-p', 'ok'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_path_full():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])
        runner.invoke(hatch, ['new', 'ko', '--basic'])
        package_dir = os.path.join(d, 'ok')
        files = find_all_files(package_dir)

        test_file = os.path.join(package_dir, 'test.pyc')
        create_file(test_file)
        assert os.path.exists(test_file)

        os.chdir(os.path.join(d, 'ko'))
        result = runner.invoke(hatch, ['clean', '-p', package_dir])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_path_full_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])

        full_path = os.path.join(d, 'ko')
        result = runner.invoke(hatch, ['clean', '-p', full_path])

        assert result.exit_code == 1
        assert 'Directory `{}` does not exist.'.format(full_path) in result.output


def test_cache():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_file(os.path.join(d, 'ok', '.cache', 'v', 'cache', 'lastfailed'))
        files = find_all_files(d)

        test_file = os.path.join(d, '.cache', 'v', 'cache', 'lastfailed')
        create_file(test_file)
        assert os.path.exists(test_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'
            '{}\n'.format(
                os.path.join(d, '.cache'),
                test_file
            )
        ) in result.output
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_coverage():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_file(os.path.join(d, 'ok', '.coverage'))
        files = find_all_files(d)

        test_file = os.path.join(d, '.coverage')
        create_file(test_file)
        assert os.path.exists(test_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'.format(test_file)
        ) in result.output
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_eggs():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_file(os.path.join(d, 'ok', '.eggs', 'ok.egg'))
        files = find_all_files(d)

        test_file = os.path.join(d, '.eggs', 'ok.egg')
        create_file(test_file)
        assert os.path.exists(test_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'
            '{}\n'.format(
                os.path.join(d, '.eggs'),
                test_file
            )
        ) in result.output
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_tox():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_file(os.path.join(d, 'ok', '.tox', 'dist', 'ok.zip'))
        files = find_all_files(d)

        test_file = os.path.join(d, '.tox', 'dist', 'ok.zip')
        create_file(test_file)
        assert os.path.exists(test_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'
            '{}\n'.format(
                os.path.join(d, '.tox'),
                test_file
            )
        ) in result.output
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_build():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_file(os.path.join(d, 'ok', 'build', 'lib', 'ok', 'ok.py'))
        files = find_all_files(d)

        test_file = os.path.join(d, 'build', 'lib', 'ok', 'ok.py')
        create_file(test_file)
        assert os.path.exists(test_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'
            '{}\n'.format(
                os.path.join(d, 'build'),
                test_file
            )
        ) in result.output
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_dist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_file(os.path.join(d, 'ok', 'dist', 'ok.whl'))
        files = find_all_files(d)

        test_file = os.path.join(d, 'dist', 'ok.whl')
        create_file(test_file)
        assert os.path.exists(test_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'
            '{}\n'.format(
                os.path.join(d, 'dist'),
                test_file
            )
        ) in result.output
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_egg_info():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_file(os.path.join(d, 'ok', 'ok.egg-info', 'PKG-INFO'))
        files = find_all_files(d)

        test_file = os.path.join(d, 'ok.egg-info', 'PKG-INFO')
        create_file(test_file)
        assert os.path.exists(test_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'
            '{}\n'.format(
                os.path.join(d, 'ok.egg-info'),
                test_file
            )
        ) in result.output
        assert not os.path.exists(test_file)
        assert_files_exist(files)


def test_pycache():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        files = find_all_files(d)

        root_file = os.path.join(d, '__pycache__', 'ok.txt')
        create_file(root_file)
        assert os.path.exists(root_file)

        non_root_file = os.path.join(d, 'ok', '__pycache__', 'ok.txt')
        create_file(non_root_file)
        assert os.path.exists(non_root_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'
            '{}\n'
            '{}\n'
            '{}\n'.format(
                os.path.join(d, '__pycache__'),
                root_file,
                os.path.join(d, 'ok', '__pycache__'),
                non_root_file
            )
        ) in result.output
        assert not os.path.exists(root_file)
        assert not os.path.exists(non_root_file)
        assert_files_exist(files)


def test_pyc():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        files = find_all_files(d)

        root_file = os.path.join(d, 'ok.pyc')
        create_file(root_file)
        assert os.path.exists(root_file)

        non_root_file = os.path.join(d, 'ok', 'ko.pyc')
        create_file(non_root_file)
        assert os.path.exists(non_root_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'
            '{}\n'.format(
                root_file,
                non_root_file
            )
        ) in result.output
        assert not os.path.exists(root_file)
        assert not os.path.exists(non_root_file)
        assert_files_exist(files)


def test_pyd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        files = find_all_files(d)

        root_file = os.path.join(d, 'ok.pyd')
        create_file(root_file)
        assert os.path.exists(root_file)

        non_root_file = os.path.join(d, 'ok', 'ko.pyd')
        create_file(non_root_file)
        assert os.path.exists(non_root_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'
            '{}\n'.format(
                root_file,
                non_root_file
            )
        ) in result.output
        assert not os.path.exists(root_file)
        assert not os.path.exists(non_root_file)
        assert_files_exist(files)


def test_pyo():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        files = find_all_files(d)

        root_file = os.path.join(d, 'ok.pyo')
        create_file(root_file)
        assert os.path.exists(root_file)

        non_root_file = os.path.join(d, 'ok', 'ko.pyo')
        create_file(non_root_file)
        assert os.path.exists(non_root_file)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Cleaned!' in result.output
        assert (
            'Removed paths:\n'
            '{}\n'
            '{}\n'.format(
                root_file,
                non_root_file
            )
        ) in result.output
        assert not os.path.exists(root_file)
        assert not os.path.exists(non_root_file)
        assert_files_exist(files)


def test_verbose_already_clean():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        files = find_all_files(d)

        result = runner.invoke(hatch, ['clean', '-v'])

        assert result.exit_code == 0
        assert 'Already clean!' in result.output
        assert_files_exist(files)
