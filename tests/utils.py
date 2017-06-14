import os
from contextlib import contextmanager
from tempfile import TemporaryDirectory


@contextmanager
def temp_chdir(cwd=None):
    with TemporaryDirectory() as d:
        origin = cwd or os.getcwd()
        os.chdir(d)
        yield d
        os.chdir(origin)
