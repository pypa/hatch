import os

from parse import parse

from hatch.create import create_package
from hatch.files.setup import TEMPLATE
from hatch.files.vc.git import get_user, get_email
from hatch.settings import copy_default_settings
from hatch.utils import temp_chdir
from .utils import read_file


def test_name():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['name'] = 'Don Quixote'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['name'] == 'Don Quixote'


def test_name_none():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['name'] = ''
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)
        expected_author = get_user() or 'U.N. Owen'

        assert parsed['name'] == expected_author


def test_email():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['email'] = 'no-reply@dev.null'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['email'] == 'no-reply@dev.null'


def test_email_none():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['email'] = ''
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)
        expected_email = get_email() or 'me@un.known'
        assert parsed['email'] == expected_email


def test_package_name():
    with temp_chdir() as d:
        settings = copy_default_settings()
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['package_name'] == 'ok'


def test_package_name_normalized():
    with temp_chdir() as d:
        settings = copy_default_settings()
        create_package(d, 'invalid-name', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['package_name_normalized'] == 'invalid_name'


def test_readme():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['readme']['format'] = 'rst'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['readme_file'] == 'README.rst'


def test_package_url():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['vc_url'] = 'https://github.com/me'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['package_url'] == 'https://github.com/me/ok'


def test_license_single():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['licenses'] = ['mit']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['license'] == 'MIT'


def test_license_multiple():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['licenses'] = ['mit', 'apache2']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['license'] == 'MIT/Apache-2.0'


def test_license_classifiers_single():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['licenses'] = ['mit']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['license_classifiers'] == "\n        'License :: OSI Approved :: MIT License',"


def test_license_classifiers_multiple():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['licenses'] = ['mit', 'apache2']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['license_classifiers'] == (
            "\n        'License :: OSI Approved :: MIT License',"
            "\n        'License :: OSI Approved :: Apache Software License',"
        )


def test_pyversions_single():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['pyversions'] = ['3.6']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['pyversions'] == "\n        'Programming Language :: Python :: 3.6',"


def test_pyversions_multiple():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['pyversions'] = ['3.6', '2.7']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['pyversions'] == (
            "\n        'Programming Language :: Python :: 2.7',"
            "\n        'Programming Language :: Python :: 3.6',"
        )


def test_pypy():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['pyversions'] = ['3.6', 'pypy3']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['pypy'] == "\n        'Programming Language :: Python :: Implementation :: PyPy',\n"


def test_pypy_none():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['pyversions'] = ['3.6']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['pypy'] == '\n'


def test_cli():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['cli'] = True
        create_package(d, 'invalid-name', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['entry_point'] == (
            '\n'
            '    entry_points={\n'
            "        'console_scripts': [\n"
            "            'invalid-name = invalid_name.cli:invalid_name',\n"
            '        ],\n'
            '    },\n'
        )


def test_cli_none():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['cli'] = False
        create_package(d, 'invalid-name', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['entry_point'] == '\n'
