import json
import subprocess

from hatch.config import get_proper_pip, get_proper_python
from hatch.utils import NEED_SUBPROCESS_SHELL, resolve_path


def get_python_path():
    return subprocess.check_output(
        [get_proper_python(), '-c', 'import sys;print(sys.executable)'], shell=NEED_SUBPROCESS_SHELL
    ).decode().strip()


def get_python_version():
    return subprocess.check_output(
        [get_proper_python(), '-c', 'import sys;print(".".join(str(i) for i in sys.version_info[:3]))'],
        shell=NEED_SUBPROCESS_SHELL
    ).decode().strip()


def get_python_implementation():
    return subprocess.check_output(
        [get_proper_python(), '-c', 'import platform;print(platform.python_implementation())'],
        shell=NEED_SUBPROCESS_SHELL
    ).decode().strip()


def install_packages(packages):
    subprocess.run([get_proper_pip(), 'install'] + packages, shell=NEED_SUBPROCESS_SHELL)


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


def get_editable_package_location(package_name=None):
    location = ''

    try:
        output = subprocess.check_output(
            [get_proper_pip(), 'list', '-e', '--format', 'columns'], shell=NEED_SUBPROCESS_SHELL
        ).decode().strip().splitlines()[2:]
    except subprocess.CalledProcessError:  # no cov
        return location

    if package_name:
        for line in output:
            name, _, path = line.split()
            if name == package_name:
                return resolve_path(path)
    else:
        if len(output) == 1:
            name, _, path = output[0].split()
            return name, resolve_path(path)
        elif len(output) > 1:
            return None, False
        else:
            return None, None

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
