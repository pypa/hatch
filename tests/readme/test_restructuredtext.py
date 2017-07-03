import os

from parse import parse

from hatch.create import create_package
from hatch.settings import DEFAULT_SETTINGS
from hatch.utils import temp_chdir
from hatch.files.readme.restructuredtext import TEMPLATE
from ..utils import read_file


def test_format():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['readme']['format'] = 'rst'
        create_package(d, 'ok', settings)

        assert os.path.exists(os.path.join(d, 'README.rst'))


def test_title():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['readme']['format'] = 'rst'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['title'] == 'ok'
        assert parsed['header_marker'] == '=='


def test_package_name():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['readme']['format'] = 'rst'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['package_name'] == 'ok'


def test_supported_versions_none():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['pyversions'] = []
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['supported_versions'] == '2.7/3.5+ and PyPy'


def test_supported_versions_py2_single():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['pyversions'] = ['2.7']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['supported_versions'] == '2.7'


def test_supported_versions_py2():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['pyversions'] = ['2.7', '2.6']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['supported_versions'] == '2.6-2.7'


def test_supported_versions_py3():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['pyversions'] = ['3.5', '3.6', '3.3', '3.4']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['supported_versions'] == '3.3+'


def test_supported_versions_all():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['pyversions'] = ['pypy3', 'pypy', '3.4', '3.3', '3.6', '3.5', '2.7']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['supported_versions'] == '2.7/3.3+ and PyPy'


def test_licenses_single():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['licenses'] = ['mit']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['license_info'] == (
            'the\n`MIT License <https://choosealicense.com/licenses/mit>`_'
        )


def test_licenses_multiple():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['licenses'] = ['mit', 'apache2']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['license_info'] == (
            'either\n\n'
            '- `MIT License <https://choosealicense.com/licenses/mit>`_\n'
            '- `Apache License, Version 2.0 <https://choosealicense.com/licenses/apache-2.0>`_'
            '\n\nat your option'
        )


def test_badges_none():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['readme']['badges'] = []
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['badges'] == '\n'


def test_badges_basic():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['badges'] == '\n'


def test_badges_single():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['readme']['badges'] = [
            {
                'image': 'https://img.shields.io/pypi/v/ok.svg',
                'target': 'https://pypi.org/project/ok'
            }
        ]
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['badges'] == (
            '\n'
            '.. image:: https://img.shields.io/pypi/v/ok.svg\n'
            '    :target: https://pypi.org/project/ok\n'
            '\n'
        )


def test_badges_multiple():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['readme']['badges'] = [
            {
                'image': 'https://img.shields.io/pypi/v/ok.svg',
                'target': 'https://pypi.org/project/ok'
            },
            {
                'image': 'https://img.shields.io/pypi/l/ok.svg',
                'target': 'https://choosealicense.com/licenses'
            }
        ]
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['badges'] == (
            '\n'
            '.. image:: https://img.shields.io/pypi/v/ok.svg\n'
            '    :target: https://pypi.org/project/ok\n'
            '\n'
            '.. image:: https://img.shields.io/pypi/l/ok.svg\n'
            '    :target: https://choosealicense.com/licenses\n'
            '\n'
        )


def test_badges_params():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['basic'] = False
        settings['readme']['badges'] = [
            {
                'image': 'https://img.shields.io/pypi/v/ok.svg',
                'target': 'https://pypi.org/project/ok',
                'style': 'flat-square'
            },
            {
                'image': 'https://img.shields.io/pypi/l/ok.svg',
                'target': 'https://choosealicense.com/licenses',
                'style': 'flat-square'
            }
        ]
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['badges'] == (
            '\n'
            '.. image:: https://img.shields.io/pypi/v/ok.svg?style=flat-square\n'
            '    :target: https://pypi.org/project/ok\n'
            '\n'
            '.. image:: https://img.shields.io/pypi/l/ok.svg?style=flat-square\n'
            '    :target: https://choosealicense.com/licenses\n'
            '\n'
        )
