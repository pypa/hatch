import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.settings import SETTINGS_FILE, copy_default_settings, save_settings
from hatch.utils import create_file, temp_chdir, temp_move_path
from ..utils import matching_file


def test_config_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['init', 'ok', '--basic'])

        assert result.exit_code == 1
        assert 'Unable to locate config file. Try `hatch config --restore`.' in result.output


def test_invalid_name():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'invalid-name', '--basic'])

        assert os.path.exists(os.path.join(d, 'invalid_name', '__init__.py'))


def test_output():
    with temp_chdir():
        runner = CliRunner()
        result = runner.invoke(hatch, ['init', 'new-project', '--basic'])

        assert result.exit_code == 0
        assert 'Created project `new-project` here' in result.output


def test_basic():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        assert os.path.exists(os.path.join(d, 'ok', '__init__.py'))
        assert os.path.exists(os.path.join(d, 'tests', '__init__.py'))
        assert os.path.exists(os.path.join(d, 'setup.py'))
        assert os.path.exists(os.path.join(d, 'requirements.txt'))
        assert os.path.exists(os.path.join(d, '.coveragerc'))
        assert os.path.exists(os.path.join(d, 'tox.ini'))
        assert matching_file(r'^LICENSE.*', os.listdir(d))
        assert matching_file(r'^README.*', os.listdir(d))


def test_cli():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--cli'])

        assert os.path.exists(os.path.join(d, 'ok', 'cli.py'))
        assert os.path.exists(os.path.join(d, 'ok', '__main__.py'))


def test_license_single():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-l', 'cc0'])

        assert os.path.exists(os.path.join(d, 'LICENSE-CC0'))


def test_license_multiple():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '-l', 'cc0,mpl'])

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

            runner.invoke(hatch, ['init', 'ok', '--basic'])

        assert os.path.exists(os.path.join(d, 'b', 'file1.txt'))
        assert os.path.exists(os.path.join(d, 'file1.txt'))
        assert os.path.exists(os.path.join(d, 'y', 'file2.txt'))
        assert not os.path.exists(os.path.join(d, 'file2.txt'))
        assert not os.path.exists(os.path.join(d, 'file.py'))
