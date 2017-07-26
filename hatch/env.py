import json
import os
import subprocess
import sys
from pathlib import Path

from hatch.utils import NEED_SUBPROCESS_SHELL

VENV_FLAGS = {
    '_HATCHING_',
    'VIRTUAL_ENV'
}


def get_proper_python():  # no cov
    if sys.platform.startswith('linux') and not VENV_FLAGS & set(os.environ):
        return 'python3'
    return 'python'


def get_proper_pip():  # no cov
    if sys.platform.startswith('linux') and not VENV_FLAGS & set(os.environ):
        return 'pip3'
    return 'pip'


def get_python_path():
    return subprocess.check_output(
        [get_proper_python(), '-c', 'import sys;print(sys.executable)'], shell=NEED_SUBPROCESS_SHELL
    ).decode().strip()


def install_packages(packages):
    subprocess.call([get_proper_pip(), 'install'] + packages, shell=NEED_SUBPROCESS_SHELL)


def get_package_version(package_name):
    output = subprocess.check_output(
        [get_proper_pip(), 'list', '--format', 'json'], shell=NEED_SUBPROCESS_SHELL
    ).decode()
    packages = json.loads(output)
    for package in packages:
        if package['name'] == package_name:
            return package['version']
    return ''


def get_editable_packages():
    output = subprocess.check_output(
        [get_proper_pip(), 'list', '-e', '--format', 'json'], shell=NEED_SUBPROCESS_SHELL
    ).decode()
    return set(package['name'] for package in json.loads(output))


def get_editable_package_location(package_name):
    location = ''

    editable_packages = get_editable_packages()
    if package_name not in editable_packages:
        return location

    output = subprocess.check_output(
        [get_proper_pip(), 'show', package_name], shell=NEED_SUBPROCESS_SHELL
    ).decode()

    for line in output.splitlines():
        if line.startswith('Location'):
            location = str(Path(line.split()[1]).resolve())

    return location


def get_installed_packages(editable=True):
    editable_packages = get_editable_packages()

    output = subprocess.check_output(
        [get_proper_pip(), 'list', '--format', 'json'], shell=NEED_SUBPROCESS_SHELL
    ).decode()
    packages = [
        package['name'] for package in json.loads(output)
        if editable or package['name'] not in editable_packages
    ]

    return packages
