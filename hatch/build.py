import subprocess

from hatch.env import get_proper_python
from hatch.utils import NEED_SUBPROCESS_SHELL, chdir


def build_package(d, universal=None, name=None, build_dir=None):
    command = [
        get_proper_python(), 'setup.py', 'bdist_wheel'
    ]

    if universal:
        command.append('--universal')

    if name:
        command.extend(['--plat-name', name])

    if build_dir:
        command.extend(['--dist-dir', build_dir])

    with chdir(d):
        result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)

    return result.returncode
