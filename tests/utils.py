import os
import re
import socket
import time

import pytest

from hatch.env import get_package_version


def wait_for_os(s=None):
    time.sleep(s or 1)


def wait_until(f, *args):  # no cov
    # There is seemingly some strange race condition when using Click's
    # test runner with commands that create a bunch of files like `env`
    # for virtualenv creation. There is a lag between the commands'
    # completion and when the OS sees the files. So, we just wait until
    # those conditions are true. #software
    end_time = time.time() + 5
    while time.time() < end_time:
        if f(*args):
            time.sleep(0.5)
            return True
        time.sleep(0.1)
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
