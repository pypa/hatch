import os

from parse import parse

from hatch.core import create_package
from hatch.readme.restructuredtext import BASE
from hatch.settings import DEFAULT_SETTINGS
from ..utils import read_file, temp_chdir


def test_readme_format():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['readme']['format'] = 'rst'
        create_package(d, 'ok', settings)

        assert os.path.exists(os.path.join(d, 'README.rst'))


def test_readme_title():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['readme']['format'] = 'rst'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'README.rst'))
        parsed = parse(BASE, contents)

        assert parsed['title'] == 'ok'
























