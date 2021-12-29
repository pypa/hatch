import os
import pathlib

from hatch.utils.fs import Path, temp_chdir, temp_directory


class TestPath:
    def test_type(self):
        expected_type = type(pathlib.Path())

        assert isinstance(Path(), expected_type)
        assert issubclass(Path, expected_type)

    def test_resolve_relative_non_existent(self, tmp_path):
        origin = os.getcwd()
        os.chdir(tmp_path)
        try:
            expected_representation = os.path.join(tmp_path, 'foo')
            assert str(Path('foo').resolve()) == expected_representation
            assert str(Path('.', 'foo').resolve()) == expected_representation
        finally:
            os.chdir(origin)

    def test_ensure_dir_exists(self, tmp_path):
        path = Path(tmp_path, 'foo')
        path.ensure_dir_exists()

        assert path.is_dir()

    def test_ensure_parent_dir_exists(self, tmp_path):
        path = Path(tmp_path, 'foo', 'bar')
        path.ensure_parent_dir_exists()

        assert path.parent.is_dir()
        assert not path.is_dir()

    def test_as_cwd(self, tmp_path):
        origin = os.getcwd()

        with Path(tmp_path).as_cwd():
            assert os.getcwd() == str(tmp_path)

        assert os.getcwd() == origin

    def test_as_cwd_env_vars(self, tmp_path):
        env_var = str(self).encode().hex().upper()
        origin = os.getcwd()

        with Path(tmp_path).as_cwd(env_vars={env_var: 'foo'}):
            assert os.getcwd() == str(tmp_path)
            assert os.environ.get(env_var) == 'foo'

        assert os.getcwd() == origin
        assert env_var not in os.environ

    def test_remove_file(self, tmp_path):
        path = Path(tmp_path, 'foo')
        path.touch()

        assert path.is_file()
        path.remove()
        assert not path.exists()

    def test_remove_directory(self, tmp_path):
        path = Path(tmp_path, 'foo')
        path.mkdir()

        assert path.is_dir()
        path.remove()
        assert not path.exists()

    def test_remove_non_existent(self, tmp_path):
        path = Path(tmp_path, 'foo')

        assert not path.exists()
        path.remove()
        assert not path.exists()

    def test_temp_hide_file(self, tmp_path):
        path = Path(tmp_path, 'foo')
        path.touch()

        with path.temp_hide() as temp_path:
            assert not path.exists()
            assert temp_path.is_file()

        assert path.is_file()
        assert not temp_path.exists()

    def test_temp_hide_dir(self, tmp_path):
        path = Path(tmp_path, 'foo')
        path.mkdir()

        with path.temp_hide() as temp_path:
            assert not path.exists()
            assert temp_path.is_dir()

        assert path.is_dir()
        assert not temp_path.exists()

    def test_temp_hide_non_existent(self, tmp_path):
        path = Path(tmp_path, 'foo')

        with path.temp_hide() as temp_path:
            assert not path.exists()
            assert not temp_path.exists()

        assert not path.exists()
        assert not temp_path.exists()


def test_temp_directory():
    with temp_directory() as temp_dir:
        assert isinstance(temp_dir, Path)
        assert temp_dir.is_dir()

    assert not temp_dir.exists()


def test_temp_chdir():
    origin = os.getcwd()

    with temp_chdir() as temp_dir:
        assert isinstance(temp_dir, Path)
        assert temp_dir.is_dir()
        assert os.getcwd() == str(temp_dir)

    assert os.getcwd() == origin
    assert not temp_dir.exists()
