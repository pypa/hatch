import subprocess

from hatch.config import get_proper_python
from hatch.utils import NEED_SUBPROCESS_SHELL, chdir


def build_package(d, build_dir, universal=None, name=None,
                  pypath=None, verbose=False):
    command = [pypath or get_proper_python(), 'setup.py']

    if not verbose:  # no cov
        command.append('--quiet')

    command.extend([
        'sdist', '--dist-dir', build_dir,
        'bdist_wheel', '--dist-dir', build_dir
    ])

    if universal:
        command.append('--universal')

    if name:
        command.extend(['--plat-name', name])

    with chdir(d):
        result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)

    return result.returncode
