import os

from parse import parse

from hatch.create import create_package
from hatch.settings import DEFAULT_SETTINGS
from hatch.utils import get_current_year, temp_chdir
from hatch.files.licenses.mit import TEMPLATE
from ..utils import read_file


def test_year():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['licenses'] = ['mit']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'LICENSE-MIT'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['year'] == get_current_year()


def test_name():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['licenses'] = ['mit']
        settings['name'] = 'Don Quixote'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'LICENSE-MIT'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['name'] == 'Don Quixote'
