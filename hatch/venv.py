import os
import sys
import shutil
import subprocess
from contextlib import contextmanager
from os.path import isfile

from appdirs import user_data_dir

from hatch.clean import remove_compiled_scripts
from hatch.exceptions import InvalidVirtualEnv
from hatch.settings import load_settings
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, env_vars, get_proper_python, get_random_venv_name,
    resolve_path
)

VENV_DIR_ISOLATED = os.path.join(user_data_dir('hatch', ''), 'venvs')
VENV_DIR_SHARED = os.path.expanduser('~{}.virtualenvs'.format(os.path.sep))
VENV_DIR = VENV_DIR_SHARED


def set_venv_dir():  # no cov
    global VENV_DIR
    venv_dir = os.environ.get('_VENV_DIR_') or load_settings(lazy=True).get('venv_dir')
    if venv_dir:
        if venv_dir == 'isolated':
            VENV_DIR = VENV_DIR_ISOLATED
        elif venv_dir == 'shared':
            VENV_DIR = VENV_DIR_SHARED
        else:
            VENV_DIR = venv_dir
    else:
        VENV_DIR = VENV_DIR_SHARED
set_venv_dir()


def is_venv(d):
    try:
        locate_exe_dir(d)
    except InvalidVirtualEnv:
        return False

    return True


def get_new_venv_name(count=1):
    if not os.path.exists(VENV_DIR):  # no cov
        if count == 1:
            return get_random_venv_name()
        else:
            return sorted(get_random_venv_name() for _ in range(count))

    current_venvs = set(p.name for p in os.scandir(VENV_DIR))
    new_venvs = set()

    while len(new_venvs) < count:
        name = get_random_venv_name()
        while name in current_venvs or name in new_venvs:  # no cov
            name = get_random_venv_name()
        new_venvs.add(name)

    return new_venvs.pop() if count == 1 else sorted(new_venvs)


def get_available_venvs():
    venvs = []

    if not os.path.exists(VENV_DIR):  # no cov
        return venvs

    for name in sorted(os.listdir(VENV_DIR)):
        venv_dir = os.path.join(VENV_DIR, name)
        if is_venv(venv_dir):
            venvs.append((name, venv_dir))

    return venvs


def create_venv(d, pypath=None, verbose=False):
    command = [sys.executable, '-m', 'virtualenv', d,
               '-p', pypath or resolve_path(shutil.which(get_proper_python()))]
    if not verbose:  # no cov
        command.append('--quiet')
    subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)


def clone_venv(origin, location):
    shutil.copytree(origin, location, copy_function=shutil.copy)
    fix_venv(location)


def fix_venv(d):
    venv_exe_dir = locate_exe_dir(d)

    for path in os.listdir(venv_exe_dir):
        fix_executable(path, venv_exe_dir)

    remove_compiled_scripts(d)


def fix_available_venvs():
    if not os.path.exists(VENV_DIR):  # no cov
        return

    for name in sorted(os.listdir(VENV_DIR)):
        try:
            fix_venv(os.path.join(VENV_DIR, name))
        except InvalidVirtualEnv:
            pass


def fix_executable(path, exe_dir):
    if not isfile(path):
        return

    with open(path, 'rb') as f:
        if f.read(2) != b'#!':
            return

    with open(path) as f:
        lines = f.readlines()

    first_line = lines[0]

    # Remove the #! and trailing whitespace.
    executable_path = first_line[2:].strip()
    if not executable_path:
        return

    # If the executable path contains spaces it will be wrapped in quotes.
    if executable_path.startswith('"'):
        path_start = executable_path.find('"') + 1
        path_end = executable_path.find('"', path_start)
        executable_path = executable_path[path_start:path_end]

        # Remove the first pair of quotes.
        first_line = first_line.replace('"', '', 2)

    # Otherwise, the executable path is whatever precedes the first space.
    else:
        executable_path = executable_path.split()[0]

    filename = os.path.basename(executable_path)

    # Removing all instances of characters in filename from the right side
    # is safe because of the path separator. Indeed, we want to remove only
    # the filename and keep the separator.
    old_path = executable_path.rstrip(filename)
    new_path = os.path.normpath(exe_dir) + os.path.sep

    first_line = first_line.replace(old_path, new_path, 1)

    if ' ' in exe_dir:
        full_path = new_path + filename
        lines[0] = first_line.replace(full_path, '"{}"'.format(full_path))
    else:
        lines[0] = first_line

    with open(path, 'w') as f:
        f.writelines(lines)


def locate_exe_dir(d):
    if os.path.exists(os.path.join(d, 'bin')):  # no cov
        return os.path.join(d, 'bin')
    elif os.path.exists(os.path.join(d, 'Scripts')):  # no cov
        return os.path.join(d, 'Scripts')
    else:
        raise InvalidVirtualEnv('Unable to locate executables directory.')


@contextmanager
def venv(d, evars=None):
    venv_exe_dir = locate_exe_dir(d)

    evars = evars or {}
    evars['_HATCHING_'] = '1'
    evars['VIRTUAL_ENV'] = d
    evars['PATH'] = '{}{}{}'.format(
        venv_exe_dir, os.pathsep, os.environ.get('PATH', '')
    )

    with env_vars(evars):
        yield venv_exe_dir
