import pytest

from hatchling.version.source.code import CodeSource


def test_no_path(isolation):
    source = CodeSource(str(isolation), {})

    with pytest.raises(ValueError, match='option `path` must be specified'):
        source.get_version_data()


def test_path_not_string(isolation):
    source = CodeSource(str(isolation), {'path': 1})

    with pytest.raises(TypeError, match='option `path` must be a string'):
        source.get_version_data()


def test_path_nonexistent(isolation):
    source = CodeSource(str(isolation), {'path': 'a/b.py'})

    with pytest.raises(OSError, match='file does not exist: a/b.py'):
        source.get_version_data()


def test_expression_not_string(temp_dir):
    source = CodeSource(str(temp_dir), {'path': 'a/b.py', 'expression': 23})

    file_path = temp_dir / 'a' / 'b.py'
    file_path.ensure_parent_dir_exists()
    file_path.touch()

    with pytest.raises(TypeError, match='option `expression` must be a string'):
        source.get_version_data()


def test_search_paths_not_array(temp_dir):
    source = CodeSource(str(temp_dir), {'path': 'a/b.py', 'search-paths': 23})

    file_path = temp_dir / 'a' / 'b.py'
    file_path.ensure_parent_dir_exists()
    file_path.touch()

    with pytest.raises(TypeError, match='option `search-paths` must be an array'):
        source.get_version_data()


def test_search_paths_entry_not_string(temp_dir):
    source = CodeSource(str(temp_dir), {'path': 'a/b.py', 'search-paths': [23]})

    file_path = temp_dir / 'a' / 'b.py'
    file_path.ensure_parent_dir_exists()
    file_path.touch()

    with pytest.raises(TypeError, match='entry #1 of option `search-paths` must be a string'):
        source.get_version_data()


def test_match_default_expression(temp_dir, helpers):
    source = CodeSource(str(temp_dir), {'path': 'a/b.py'})

    file_path = temp_dir / 'a' / 'b.py'
    file_path.ensure_parent_dir_exists()
    file_path.write_text('__version__ = "0.0.1"')

    with temp_dir.as_cwd():
        assert source.get_version_data()['version'] == '0.0.1'


def test_match_custom_expression_basic(temp_dir):
    source = CodeSource(str(temp_dir), {'path': 'a/b.py', 'expression': 'VER'})

    file_path = temp_dir / 'a' / 'b.py'
    file_path.ensure_parent_dir_exists()
    file_path.write_text('VER = "0.0.1"')

    with temp_dir.as_cwd():
        assert source.get_version_data()['version'] == '0.0.1'


def test_match_custom_expression_complex(temp_dir, helpers):
    source = CodeSource(str(temp_dir), {'path': 'a/b.py', 'expression': 'foo()'})

    file_path = temp_dir / 'a' / 'b.py'
    file_path.ensure_parent_dir_exists()
    file_path.write_text(
        helpers.dedent(
            """
            __version_info__ = (1, 0, 0, 1, 'dev0')

            def foo():
                return '.'.join(str(part) for part in __version_info__)
            """
        )
    )

    with temp_dir.as_cwd():
        assert source.get_version_data()['version'] == '1.0.0.1.dev0'


def test_search_paths(temp_dir, helpers):
    source = CodeSource(str(temp_dir), {'path': 'a/b.py', 'search-paths': ['.']})

    parent_dir = temp_dir / 'a'
    parent_dir.mkdir()
    (parent_dir / '__init__.py').touch()
    (parent_dir / 'b.py').write_text(
        helpers.dedent(
            """
            from a.c import foo

            __version__ = foo((1, 0, 0, 1, 'dev0'))
            """
        )
    )
    (parent_dir / 'c.py').write_text(
        helpers.dedent(
            """
            def foo(version_info):
                return '.'.join(str(part) for part in version_info)
            """
        )
    )

    with temp_dir.as_cwd():
        assert source.get_version_data()['version'] == '1.0.0.1.dev0'
