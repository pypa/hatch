import os

from parse import parse

from hatch.core import create_package
from hatch.settings import DEFAULT_SETTINGS
from ..utils import temp_chdir


def test_readme_format():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['readme']['format'] = 'rst'
        create_package(d, 'ok', settings)
