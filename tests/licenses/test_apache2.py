import os

from parse import parse

from hatch.create import create_package
from hatch.settings import DEFAULT_SETTINGS
from hatch.utils import get_current_year
from hatch.licenses.apache2 import TEMPLATE
from ..utils import read_file, temp_chdir


def test_year():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['licenses'] = ['apache2']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'LICENSE-APACHE'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['year'] == get_current_year()


def test_name():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['licenses'] = ['apache2']
        settings['name'] = 'Don Quixote'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'LICENSE-APACHE'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['name'] == 'Don Quixote'
