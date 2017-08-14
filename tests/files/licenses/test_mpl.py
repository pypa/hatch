import os

from parse import parse

from hatch.create import create_package
from hatch.settings import copy_default_settings
from hatch.utils import get_current_year, temp_chdir
from hatch.files.licenses.mpl import TEMPLATE
from ...utils import read_file


def test_year():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['licenses'] = ['mpl']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'LICENSE-MPL'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['year'] == get_current_year()


def test_name():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['licenses'] = ['mpl']
        settings['name'] = 'Red Panda'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'LICENSE-MPL'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['name'] == 'Red Panda'
