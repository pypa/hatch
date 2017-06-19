import os

from click.testing import CliRunner

from hatch.cli import hatch
from .utils import matching_file, temp_chdir


def test_invalid_name():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'invalid-name', '--basic'])

        assert os.path.exists(os.path.join(d, 'invalid_name', '__init__.py'))


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
