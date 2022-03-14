from itertools import product

import pytest

from hatchling.version.source.regex import RegexSource

DEFAULT_PATTERN_PRODUCTS = list(product(('__version__', 'VERSION', 'version'), ('"', "'"), ('', 'v')))


def test_no_path(isolation):
    source = RegexSource(str(isolation), {})

    with pytest.raises(ValueError, match='option `path` must be specified'):
        source.get_version_data()


def test_path_not_string(isolation):
    source = RegexSource(str(isolation), {'path': 1})

    with pytest.raises(TypeError, match='option `path` must be a string'):
        source.get_version_data()


def test_path_nonexistent(isolation):
    source = RegexSource(str(isolation), {'path': 'a/b'})

    with pytest.raises(OSError, match='file does not exist: a/b'):
        source.get_version_data()


def test_pattern_not_string(temp_dir):
    source = RegexSource(str(temp_dir), {'path': 'a/b', 'pattern': 23})

    file_path = temp_dir / 'a' / 'b'
    file_path.ensure_parent_dir_exists()
    file_path.touch()

    with pytest.raises(TypeError, match='option `pattern` must be a string'):
        source.get_version_data()


def test_no_version(temp_dir):
    source = RegexSource(str(temp_dir), {'path': 'a/b'})

    file_path = temp_dir / 'a' / 'b'
    file_path.ensure_parent_dir_exists()
    file_path.touch()

    with temp_dir.as_cwd():
        with pytest.raises(ValueError, match='unable to parse the version from the file: a/b'):
            source.get_version_data()


def test_pattern_no_version_group(temp_dir):
    source = RegexSource(str(temp_dir), {'path': 'a/b', 'pattern': '.+'})

    file_path = temp_dir / 'a' / 'b'
    file_path.ensure_parent_dir_exists()
    file_path.write_text('foo')

    with temp_dir.as_cwd():
        with pytest.raises(ValueError, match='no group named `version` was defined in the pattern'):
            source.get_version_data()


def test_match_custom_pattern(temp_dir):
    source = RegexSource(str(temp_dir), {'path': 'a/b', 'pattern': 'VER = "(?P<version>.+)"'})

    file_path = temp_dir / 'a' / 'b'
    file_path.ensure_parent_dir_exists()
    file_path.write_text('VER = "0.0.1"')

    with temp_dir.as_cwd():
        assert source.get_version_data()['version'] == '0.0.1'


@pytest.mark.parametrize('variable, quote, prefix', DEFAULT_PATTERN_PRODUCTS)
def test_match_default_pattern(temp_dir, helpers, variable, quote, prefix):
    source = RegexSource(str(temp_dir), {'path': 'a/b'})

    file_path = temp_dir / 'a' / 'b'
    file_path.ensure_parent_dir_exists()
    file_path.write_text(
        helpers.dedent(
            f"""
            __all__ = [{quote}{variable}{quote}, {quote}foo{quote}]

            {variable} = {quote}{prefix}0.0.1{quote}

            def foo():
                return {quote}bar{quote}
            """
        )
    )

    with temp_dir.as_cwd():
        assert source.get_version_data()['version'] == '0.0.1'


@pytest.mark.parametrize('variable, quote, prefix', DEFAULT_PATTERN_PRODUCTS)
def test_set_default_pattern(temp_dir, helpers, variable, quote, prefix):
    source = RegexSource(str(temp_dir), {'path': 'a/b'})

    file_path = temp_dir / 'a' / 'b'
    file_path.ensure_parent_dir_exists()
    file_path.write_text(
        helpers.dedent(
            f"""
            __all__ = [{quote}{variable}{quote}, {quote}foo{quote}]

            {variable} = {quote}{prefix}0.0.1{quote}

            def foo():
                return {quote}bar{quote}
            """
        )
    )

    with temp_dir.as_cwd():
        source.set_version('foo', source.get_version_data())
        assert source.get_version_data()['version'] == 'foo'
