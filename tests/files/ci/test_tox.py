import os

from parse import parse

from hatch.create import create_package
from hatch.settings import copy_default_settings
from hatch.utils import temp_chdir
from hatch.files.ci.tox import TEMPLATE
from ...utils import read_file


def test_build_matrix_single():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['pyversions'] = ['3.6']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'tox.ini'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['build_matrix'] == '\n    py36,'


def test_build_matrix_multiple():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['pyversions'] = ['2.7', '3.6']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'tox.ini'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['build_matrix'] == (
            '\n    py27,'
            '\n    py36,'
        )


def test_pypy():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['pyversions'] = ['3.6', 'pypy', 'pypy3']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'tox.ini'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['build_matrix'] == (
            '\n    py36,'
            '\n    pypy,'
            '\n    pypy3,'
        )


def test_coverage_package():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['coverage'] = 'codecov'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'tox.ini'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['coverage_package'] == '\n    codecov\n'


def test_coverage_package_none():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['coverage'] = ''
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'tox.ini'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['coverage_package'] == '\n'
