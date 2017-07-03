import os

from hatch.utils import create_file, temp_chdir
from .utils import matching_file


def test_matching_file():
    with temp_chdir() as d:
        create_file(os.path.join(d, 'file.txt'))
        files = os.listdir(d)
        assert matching_file(r'^fi.+t$', files)
        assert not matching_file(r'\.json$', files)
