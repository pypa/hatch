import os
import subprocess
from contextlib import contextmanager

from appdirs import user_data_dir

from hatch.env import get_python_path
from hatch.utils import NEED_SUBPROCESS_SHELL, env_vars

VENV_DIR = os.path.join(user_data_dir('hatch', ''), 'venvs')


def create_venv(d, pypath=None):
    command = ['virtualenv', d, '-p', pypath or get_python_path()]
    subprocess.call(command, shell=NEED_SUBPROCESS_SHELL)


@contextmanager
def venv(d, evars=None):
    if os.path.exists(os.path.join(d, 'bin')):  # no cov
        venv_exe_dir = os.path.join(d, 'bin')
    elif os.path.exists(os.path.join(d, 'Scripts')):  # no cov
        venv_exe_dir = os.path.join(d, 'Scripts')
    else:
        raise OSError('Unable to locate executables directory.')

    evars = evars or {}
    evars['PATH'] = '{}{}{}'.format(
        venv_exe_dir, os.pathsep, os.environ.get('PATH', '')
    )

    hatch_level = int(os.environ.get('HATCH_LEVEL', 0))
    evars['_HATCH_LEVEL_'] = str(hatch_level + 1)

    with env_vars(evars):
        yield
