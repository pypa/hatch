import os

from parse import parse

from hatch.create import create_package
from hatch.settings import copy_default_settings
from hatch.utils import get_current_year, temp_chdir
from hatch.files.licenses.cc0 import TEMPLATE
from ...utils import read_file


def test_year():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['licenses'] = ['cc0']
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'LICENSE-CC0'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['year'] == get_current_year()


def test_name():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['licenses'] = ['cc0']
        settings['name'] = 'Guy Fawkes'
        create_package(d, 'ok', settings)

        contents = read_file(os.path.join(d, 'LICENSE-CC0'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['name'] == 'Guy Fawkes'
