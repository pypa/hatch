import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import install_packages
from hatch.utils import temp_chdir
from hatch.venv import create_venv, venv
from .utils import read_file


def create_test_passing(d):
    with open(os.path.join(d, 'tests', 'test_add.py'), 'w') as f:
        f.write(
            'def test_add():\n'
            '    assert 1 + 2 == 3\n'
        )


def create_test_failing(d):
    with open(os.path.join(d, 'tests', 'test_add.py'), 'w') as f:
        f.write(
            'def test_add():\n'
            '    assert 1 + 2 != 3\n'
        )


def test_package_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_test_passing(d)

        result = runner.invoke(hatch, ['test'])

        raise result.exception
        assert result.exit_code == 0
        assert '1 passed' in result.output


















