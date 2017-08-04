import os

from parse import parse

from hatch.create import create_package
from hatch.settings import copy_default_settings
from hatch.utils import temp_chdir
from hatch.files.ignore.git import TEMPLATE
from ...utils import read_file


def test_package_name():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['vc'] = 'git'
        create_package(d, 'invalid-name', settings)

        contents = read_file(os.path.join(d, '.gitignore'))
        parsed = parse(TEMPLATE, contents)

        assert parsed['package_name_normalized'] == 'invalid_name'
