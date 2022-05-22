import os

from hatchling.utils.fs import path_to_uri


def test_path_to_uri(isolation, uri_slash_prefix):
    bad_path = f'{isolation}{os.sep}'
    normalized_path = str(isolation).replace(os.sep, '/')
    assert path_to_uri(bad_path) == f'file:{uri_slash_prefix}{normalized_path}'
