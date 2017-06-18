import os

from parse import parse

from hatch.core import create_package
from hatch.readme.restructuredtext import BASE
from hatch.settings import DEFAULT_SETTINGS
from ..utils import read_file, temp_chdir


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
        parsed = parse(BASE, contents)

        assert parsed['title'] == 'ok'
        assert parsed['header_marker'] == '=='


def test_package_name():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['readme']['format'] = 'rst'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(BASE, contents)

        assert parsed['package_name'] == 'ok'


def test_supported_versions_py2():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['pyversions'] = ['2.7', '2.6']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(BASE, contents)

        assert parsed['supported_versions'] == '2.6-2.7'


def test_supported_versions_py3():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['pyversions'] = ['3.5', '3.6', '3.3', '3.4']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(BASE, contents)

        assert parsed['supported_versions'] == '3.3+'


def test_supported_versions_all():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['pyversions'] = ['pypy3', 'pypy', '3.6', '3.5', '2.7']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(BASE, contents)

        assert parsed['supported_versions'] == '2.7/3.5+ and PyPy'


def test_single_license():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['licenses'] = ['mit']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(BASE, contents)

        assert parsed['license_info'] == (
            'the\n`MIT License <https://choosealicense.com/licenses/mit>`_'
        )


def test_multiple_licenses():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['licenses'] = ['mit', 'apache2']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(BASE, contents)

        assert parsed['license_info'] == (
            'either\n\n'
            '- `MIT License <https://choosealicense.com/licenses/mit>`_\n'
            '- `Apache License, Version 2.0 <https://choosealicense.com/licenses/apache-2.0>`_'
            '\n\nat your option'
        )
























