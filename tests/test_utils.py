import os

from hatch.utils import (
    chdir, create_file, get_current_year, normalize_package_name, remove_path,
    temp_chdir, temp_move_path
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
