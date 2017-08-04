import os

from hatch.create import create_package
from hatch.settings import copy_default_settings
from hatch.utils import temp_chdir
from ...utils import read_file


def test_setup():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['vc'] = 'git'
        create_package(d, 'ok', settings)

        assert os.path.exists(os.path.join(d, '.git'))
        assert os.path.exists(os.path.join(d, '.gitattributes'))
        assert os.path.exists(os.path.join(d, '.gitignore'))


def test_gitattributes():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['vc'] = 'git'
        create_package(d, 'ok', settings)

        assert read_file(os.path.join(d, '.gitattributes')) == (
            '# Auto detect text files and perform LF normalization\n'
            '* text=auto\n'
        )
