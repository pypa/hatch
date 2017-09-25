import os
import re
import socket
import time
import traceback

import pytest

from hatch.env import get_package_version


def print_traceback(exc_info):  # no cov
    traceback.print_exception(*exc_info)


def wait_for_os(s=None):
    time.sleep(s or 1)


def wait_until(f, *args):  # no cov
    # https://github.com/kennethreitz/pipenv/pull/403
    end_time = time.time() + 600
    while time.time() < end_time:
        if f(*args):
            time.sleep(0.5)
            return True
        time.sleep(0.2)
    raise AssertionError('timeout')


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
