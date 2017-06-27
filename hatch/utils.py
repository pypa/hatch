import shutil
import json
import os
import platform
import re
import subprocess
from datetime import datetime

NEED_SUBPROCESS_SHELL = False

if os.name == 'nt' or platform.system() == 'Windows':  # no cov
    NEED_SUBPROCESS_SHELL = True


def get_python_path():
    return subprocess.check_output(
        ['python', '-c', 'import sys;print(sys.executable)'], shell=NEED_SUBPROCESS_SHELL
    ).decode().strip()


def install_packages(packages):
    subprocess.call(['pip', 'install'] + packages, shell=NEED_SUBPROCESS_SHELL)


def get_package_version(package_name):
    output = subprocess.check_output(
        ['pip', 'list', '--format', 'json'], shell=NEED_SUBPROCESS_SHELL
    ).decode()
    packages = json.loads(output)
    for package in packages:
        if package['name'] == package_name:
            return package['version']
    return ''


def get_installed_packages(editable=True):
    output = subprocess.check_output(
        ['pip', 'list', '-e', '--format', 'json'], shell=NEED_SUBPROCESS_SHELL
    ).decode()
    editable_packages = set(package['name'] for package in json.loads(output))

    output = subprocess.check_output(
        ['pip', 'list', '--format', 'json'], shell=NEED_SUBPROCESS_SHELL
    ).decode()
    packages = [
        package['name'] for package in json.loads(output)
        if editable or package['name'] not in editable_packages
    ]

    return packages


def ensure_dir_exists(d):
    if not os.path.exists(d):
        os.makedirs(d)


def create_file(fname):
    ensure_dir_exists(os.path.dirname(fname))
    with open(fname, 'a'):
        os.utime(fname, times=None)


def get_current_year():
    return str(datetime.now().year)


def normalize_package_name(package_name):
    return re.sub(r"[-_.]+", "_", package_name).lower()
