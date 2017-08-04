import os

from parse import parse

from hatch.create import create_package
from hatch.settings import copy_default_settings
from hatch.utils import temp_chdir
from hatch.files.coverage.coveragerc import TEMPLATE
from ...utils import read_file


def test_package_name():
    with temp_chdir() as d:
        settings = copy_default_settings()
        create_package(d, 'invalid-name', settings)

        contents = read_file(os.path.join(d, '.coveragerc'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['package_name_normalized'] == 'invalid_name'


def test_cli():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['cli'] = True
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.coveragerc'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['cli_file'] == '__main__'


def test_cli_none():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['cli'] = False
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.coveragerc'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['cli_file'] == 'cli'
