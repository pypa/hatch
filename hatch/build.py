import subprocess

from hatch.utils import NEED_SUBPROCESS_SHELL, chdir, get_proper_python


def build_package(d, universal=None, name=None, build_dir=None, pypath=None):
    command = [
        pypath or get_proper_python(), 'setup.py', 'sdist'
    ]

    if build_dir:
        command.extend(['--dist-dir', build_dir])

    command.append('bdist_wheel')

    if build_dir:
        command.extend(['--dist-dir', build_dir])

    if universal:
        command.append('--universal')

    if name:
        command.extend(['--plat-name', name])

    with chdir(d):
        result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)

    return result.returncode
