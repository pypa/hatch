import os

from hatch.utils import (
    chdir, create_file, get_current_year, normalize_package_name, temp_chdir
)


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
