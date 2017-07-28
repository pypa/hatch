import os
import platform
import re
from datetime import datetime
from contextlib import contextmanager
from tempfile import TemporaryDirectory

NEED_SUBPROCESS_SHELL = False

if os.name == 'nt' or platform.system() == 'Windows':  # no cov
    NEED_SUBPROCESS_SHELL = True


def ensure_dir_exists(d):
    if not os.path.exists(d):
        os.makedirs(d)


def create_file(fname):
    ensure_dir_exists(os.path.dirname(os.path.abspath(fname)))
    with open(fname, 'a'):
        os.utime(fname, times=None)


def get_current_year():
    return str(datetime.now().year)


def normalize_package_name(package_name):
    return re.sub(r"[-_.]+", "_", package_name).lower()


@contextmanager
def chdir(d, cwd=None):
    origin = cwd or os.getcwd()
    os.chdir(d)

    try:
        yield
    finally:
        os.chdir(origin)


@contextmanager
def temp_chdir(cwd=None):
    with TemporaryDirectory() as d:
        origin = cwd or os.getcwd()
        os.chdir(d)

        try:
            yield d
        finally:
            os.chdir(origin)


@contextmanager
def env_vars(evars):
    for ev in evars:
        os.environ[ev] = evars[ev]

    try:
        yield
    finally:
        for ev in evars:
            os.environ.pop(ev)
