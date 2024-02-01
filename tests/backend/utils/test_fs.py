import os

from hatchling.utils.fs import path_to_uri


class TestPathToURI:
    def test_unix(self, isolation, uri_slash_prefix):
        bad_path = f'{isolation}{os.sep}'
        normalized_path = str(isolation).replace(os.sep, '/')
        assert path_to_uri(bad_path) == f'file:{uri_slash_prefix}{normalized_path}'

    def test_character_escaping(self, temp_dir, uri_slash_prefix):
        path = temp_dir / 'foo bar'
        normalized_path = str(path).replace(os.sep, '/').replace(' ', '%20')
        assert path_to_uri(path) == f'file:{uri_slash_prefix}{normalized_path}'
