import os

import pytest

from hatch.create import create_package
from hatch.settings import copy_default_settings
from hatch.utils import (
    chdir, create_file, download_file, get_current_year, get_random_venv_name,
    get_requirements_file, is_setup_managed, normalize_package_name, parse_setup,
    remove_path, temp_chdir, temp_move_path
)


def test_get_random_venv_name():
    assert isinstance(get_random_venv_name(), str)
    assert 3 <= len(get_random_venv_name()) <= 5


class TestGetRequirementsFile:
    def test_default_exists(self):
        with temp_chdir() as d:
            file = os.path.join(d, 'requirements.txt')
            create_file(file)
            assert get_requirements_file(d) == file

    def test_default_not_exists(self):
        with temp_chdir() as d:
            assert get_requirements_file(d) is None

    def test_default_exists_dev_exists(self):
        with temp_chdir() as d:
            file1 = os.path.join(d, 'requirements.txt')
            file2 = os.path.join(d, 'dev-requirements.txt')
            create_file(file1)
            create_file(file2)
            assert get_requirements_file(d) == file1

    def test_default_not_exists_dev_exists(self):
        with temp_chdir() as d:
            file = os.path.join(d, 'dev-requirements.txt')
            create_file(file)
            assert get_requirements_file(d) == file

    def test_default_exists_dev_exists_dev_only(self):
        with temp_chdir() as d:
            file1 = os.path.join(d, 'requirements.txt')
            file2 = os.path.join(d, 'requirementss.txt')
            create_file(file1)
            create_file(file2)
            assert get_requirements_file(d, dev=True) == file2


def test_get_current_year():
    year = get_current_year()
    assert len(year) >= 4
    assert int(year) >= 2017


def test_normalize_package_name():
    assert normalize_package_name('aN___inVaLiD..pAckaGe---naME') == 'an_invalid_package_name'


def test_chdir():
    origin = os.getcwd()
    parent_dir = os.path.dirname(os.path.abspath(origin))
    with chdir(parent_dir):
        assert os.getcwd() == parent_dir

    assert os.getcwd() == origin


def test_temp_chdir():
    with temp_chdir() as d:
        create_file(os.path.join(d, 'file.txt'))

    assert not os.path.exists(d)


def test_download_file():
    with temp_chdir() as d:
        fname = os.path.join(d, 'file.txt')
        download_file('https://httpbin.org/bytes/1024', fname)
        with open(fname, 'rb') as f:
            assert len(f.read()) == 1024


def test_remove_path_not_exist():
    with temp_chdir() as d:
        remove_path(os.path.join(d, 'file.txt'))


def test_temp_move_path():
    with temp_chdir() as d1:
        path = os.path.join(d1, 'test')
        create_file(path)
        assert os.path.exists(path)

        with temp_chdir() as d2:
            with temp_move_path(path, d2) as dst:
                assert not os.path.exists(path)
                assert dst == os.path.join(d2, 'test')

        assert os.path.exists(path)


def test_temp_move_path_not_exist():
    with temp_chdir() as d:
        with temp_move_path(os.path.join(d, 'test'), d):
            pass


def test_is_setup_managed():
    with temp_chdir() as d:
        settings = copy_default_settings()
        create_package(d, 'ok', settings)

        assert is_setup_managed(os.path.join(d, 'setup.py')) is True
        assert is_setup_managed(os.path.join(d, 'pyproject.toml')) is False
        assert is_setup_managed(os.path.join(d, 'non-existent-file')) is False


def test_parse_setup():
    # pass in a unmanaged file and watch it fumble
    # pass in a managed file with wrong user section
    # pass in a managed file and check for user section and everything else
    # pass in a non-existent file
    with temp_chdir() as d:
        settings = copy_default_settings()
        create_package(d, 'ok', settings)

        assert parse_setup(os.path.join(d, 'setup.py')) == '\n'

        faulty_setup_contents = '########## BEGIN USER OVERRIDES #######\n'
        with open(os.path.join(d, 'faulty_setup.py'), 'w') as f:
            f.write(faulty_setup_contents)
        with pytest.raises(FileNotFoundError):
            parse_setup(os.path.join(d, 'non-existent-file'))
        with pytest.raises(Exception, message='User-defined section did not end correctly.'):
            parse_setup(os.path.join(d, 'pyproject.toml'))
        with pytest.raises(Exception, message='User-defined section did not end correctly.'):
            parse_setup(os.path.join(d, 'faulty_setup.py'))
