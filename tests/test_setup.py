import os

from parse import parse

from hatch.core import create_package
from hatch.settings import DEFAULT_SETTINGS
from hatch.setup import TEMPLATE
from .utils import read_file, temp_chdir


def test_name():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['name'] = 'Don Quixote'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['name'] == 'Don Quixote'


def test_name_none():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['name'] = ''
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['name'] == 'U.N. Owen'


def test_email():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['email'] = 'no-reply@dev.null'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['email'] == 'no-reply@dev.null'


def test_email_none():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['email'] = ''
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['email'] == 'me@un.known'


def test_package_name():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['package_name'] == 'ok'


def test_package_name_normalized():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        create_package(d, 'invalid-name', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['package_name_normalized'] == 'invalid_name'


def test_readme():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['readme']['format'] = 'rst'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'setup.py'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['readme_file'] == 'README.rst'



















