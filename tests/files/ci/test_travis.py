import os

from parse import parse

from hatch.create import create_package
from hatch.settings import copy_default_settings
from hatch.utils import temp_chdir
from hatch.files.ci.travis import TEMPLATE
from ...utils import read_file


def test_basic():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = True
        settings['ci'] = ['travis']
        settings['pyversions'] = ['3.6']
        create_package(d, 'ok', settings)

        assert not os.path.exists(os.path.join(d, '.travis.yml'))


def test_build_matrix_single():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['pyversions'] = ['3.6']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['build_matrix'] == (
            '\n        - python: 3.6'
            '\n          env: TOXENV=py36'
        )


def test_build_matrix_multiple():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['pyversions'] = ['2.7', '3.6']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['build_matrix'] == (
            '\n        - python: 2.7'
            '\n          env: TOXENV=py27'
            '\n        - python: 3.6'
            '\n          env: TOXENV=py36'
        )


def test_build_matrix_pypy():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['pyversions'] = ['pypy']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['build_matrix'] == (
            '\n        - python: pypy2.7-5.8.0'
            '\n          env: TOXENV=pypy'
        )


def test_build_matrix_pypy3():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['pyversions'] = ['pypy3']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['build_matrix'] == (
            '\n        - python: pypy3.5-5.8.0'
            '\n          env: TOXENV=pypy3'
        )


def test_build_matrix_mixed():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['pyversions'] = ['3.6', '2.7', 'pypy3', 'pypy']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['build_matrix'] == (
            '\n        - python: 2.7'
            '\n          env: TOXENV=py27'
            '\n        - python: 3.6'
            '\n          env: TOXENV=py36'
            '\n        - python: pypy2.7-5.8.0'
            '\n          env: TOXENV=pypy'
            '\n        - python: pypy3.5-5.8.0'
            '\n          env: TOXENV=pypy3'
        )


def test_coverage_package():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['coverage'] = 'codecov'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['coverage_package'] == ' codecov\n'


def test_coverage_package_none():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['coverage'] = ''
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['coverage_package'] == '\n'


def test_coverage_command():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['coverage'] = 'codecov'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['coverage_command'] == '\n\nafter_success:\n  - codecov'


def test_coverage_command_none():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['basic'] = False
        settings['ci'] = ['travis']
        settings['coverage'] = ''
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, '.travis.yml'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['coverage_command'] == '\n'
