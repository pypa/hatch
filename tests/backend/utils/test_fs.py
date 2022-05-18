import os

from hatchling.utils.fs import path_to_uri


def test_path_to_uri(isolation):
    assert path_to_uri(isolation) == f'file://{str(isolation).replace(os.sep, "/")}'
