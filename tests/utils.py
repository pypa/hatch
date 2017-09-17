import os
import re
import socket
import time

import pytest

from hatch.env import get_package_version


def wait_for_os():
    time.sleep(0.1)


def get_version_as_bytes(package_name):
    return bytes(
        int(s) for s in get_package_version(package_name).split('.')
    )


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def matching_file(pattern, files):
    for file in files:
        if re.search(pattern, file):
            return True
    return False


def connected_to_internet():  # no cov
    if os.environ.get('CI') and os.environ.get('TRAVIS'):
        return True
    try:
        # Test availability of DNS first
        host = socket.gethostbyname('www.google.com')
        # Test connection
        socket.create_connection((host, 80), 2)
        return True
    except:
        return False


requires_internet = pytest.mark.skipif(not connected_to_internet(),
                                       reason='Not connected to internet')
