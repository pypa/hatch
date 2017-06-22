import os

from hatch.create import create_package
from hatch.settings import DEFAULT_SETTINGS
from ..utils import read_file, temp_chdir


def test_setup():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['vc'] = 'git'
        create_package(d, 'ok', settings)

        assert os.path.exists(os.path.join(d, '.git'))
        assert os.path.exists(os.path.join(d, '.gitattributes'))
        assert os.path.exists(os.path.join(d, '.gitignore'))


def test_gitattributes():
    with temp_chdir() as d:
        settings = DEFAULT_SETTINGS.copy()
        settings['vc'] = 'git'
        create_package(d, 'ok', settings)

        assert read_file(os.path.join(d, '.gitattributes')) == (
            '# Auto detect text files and perform LF normalization\n'
            '* text=auto\n'
        )
