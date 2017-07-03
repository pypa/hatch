import re

from hatch.env import get_package_version


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
