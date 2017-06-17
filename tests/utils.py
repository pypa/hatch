import os
import re
from contextlib import contextmanager
from tempfile import TemporaryDirectory


def matching_file(pattern, files):
    for file in files:
        if re.match(pattern, file):
            return True
    return False


@contextmanager
def temp_chdir(cwd=None):
    with TemporaryDirectory() as d:
        origin = cwd or os.getcwd()
        os.chdir(d)
        yield d
        os.chdir(origin)
