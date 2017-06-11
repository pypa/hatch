import os
import re
from datetime import datetime


def create_file(fname):
    base_dir = os.path.dirname(fname)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    with open(fname, 'a'):
        os.utime(fname, times=None)


def get_current_year():
    return str(datetime.now().year)


def normalize_package_name(package_name):
    return re.sub(r"[-_.]+", "_", package_name).lower()
