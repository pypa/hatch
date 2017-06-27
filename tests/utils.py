import os
import re
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from hatch.utils import get_package_version


def get_version_as_bytes():
    return bytes(
        int(s) for s in get_package_version('requests').split('.')
    )


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def matching_file(pattern, files):
    for file in files:
        if re.search(pattern, file):
            return True
    return False


@contextmanager
def temp_chdir(cwd=None):
    with TemporaryDirectory() as d:
        origin = cwd or os.getcwd()
        os.chdir(d)

        try:
            yield d
        finally:
            os.chdir(origin)
