import os

from hatch.create import create_package
from hatch.settings import DEFAULT_SETTINGS
from .utils import read_file, temp_chdir


def test_package_init():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['cli'] = True
        create_package(d, 'invalid-name', settings)

        assert read_file(os.path.join(d, 'invalid_name', '__init__.py')) == (
            "__version__ = '0.0.1'\n"
        )


def test_tests_init():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['cli'] = True
        create_package(d, 'invalid-name', settings)

        assert os.path.exists(os.path.join(d, 'tests', '__init__.py'))


def test_cli():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['cli'] = True
        create_package(d, 'invalid-name', settings)

        assert read_file(os.path.join(d, 'invalid_name', 'cli.py')) == (
            'def invalid_name():\n'
            '    pass\n'
        )


def test_cli_none():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['cli'] = False
        create_package(d, 'invalid-name', settings)

        assert not os.path.exists(os.path.join(d, 'invalid_name', 'cli.py'))
