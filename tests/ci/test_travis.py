import os

from parse import parse

from hatch.create import create_package
from hatch.settings import DEFAULT_SETTINGS
from hatch.files.ci.travis import TEMPLATE
from ..utils import read_file, temp_chdir


def test_basic():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = True
        settings['ci'] = ['travis']
        settings['pyversions'] = ['3.6']
        create_package(d, 'ok', settings)

        assert not os.path.exists(os.path.join(d, '.travis.yml'))


def test_build_matrix_single():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['pyversions'] = ['3.6']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['build_matrix'] == (
            '\n        - python: 3.6'
            '\n          env: TOXENV=36'
        )


def test_build_matrix_multiple():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['pyversions'] = ['2.7', '3.6']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['build_matrix'] == (
            '\n        - python: 2.7'
            '\n          env: TOXENV=27'
            '\n        - python: 3.6'
            '\n          env: TOXENV=36'
        )


def test_pypy_install():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['pyversions'] = ['3.6', 'pypy']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)
        pypy_install = parsed['pypy_install']

        assert "$TRAVIS_PYTHON_VERSION == 'pypy'" in pypy_install
        assert pypy_install.count('-portable') == 3


def test_pypy3_install():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['pyversions'] = ['3.6', 'pypy3']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)
        pypy_install = parsed['pypy_install']

        assert "$TRAVIS_PYTHON_VERSION == 'pypy3'" in pypy_install
        assert pypy_install.count('-portable') == 3


def test_pypy_and_pypy3_install():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['pyversions'] = ['3.6', 'pypy', 'pypy3']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)
        pypy_install = parsed['pypy_install']

        assert "$TRAVIS_PYTHON_VERSION == 'pypy'" in pypy_install
        assert "$TRAVIS_PYTHON_VERSION == 'pypy3'" in pypy_install
        assert pypy_install.count('-portable') == 6


def test_coverage_package():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['coverage'] = 'codecov'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['coverage_package'] == ' codecov\n'


def test_coverage_package_none():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['coverage'] = ''
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['coverage_package'] == '\n'


def test_coverage_command():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['coverage'] = 'codecov'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['coverage_command'] == '\n\nafter_success:\n  - codecov'


def test_coverage_command_none():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['coverage'] = ''
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['coverage_command'] == '\n'
