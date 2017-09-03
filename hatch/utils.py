import os
import platform
import re
import shutil
from datetime import datetime
from contextlib import contextmanager
from tempfile import TemporaryDirectory

ON_WINDOWS = False
if os.name == 'nt' or platform.system() == 'Windows':  # no cov
    ON_WINDOWS = True

NEED_SUBPROCESS_SHELL = ON_WINDOWS

VENV_FLAGS = {
    '_HATCH_LEVEL_',
    'VIRTUAL_ENV',
    'CONDA_PREFIX'
}


def venv_active():
    return bool(VENV_FLAGS & set(os.environ))


def get_proper_python():  # no cov
    if not venv_active():
        default_python = os.environ.get('_DEFAULT_PYTHON_', None)
        if default_python:
            return default_python
        elif not ON_WINDOWS:
            return 'python3'
    return 'python'


def get_proper_pip():  # no cov
    if not venv_active():
        default_python = os.environ.get('_DEFAULT_PIP_', None)
        if default_python:
            return default_python
        elif not ON_WINDOWS:
            return 'pip3'
    return 'pip'


def get_admin_command():
    # The default name `Administrator` will not always be desired. In future,
    # we should allow the use of an env var to specify the admin name.
    if ON_WINDOWS:
        return [
            'runas', r'/user:{}\{}'.format(
                platform.node() or os.environ.get('USERDOMAIN', ''),
                'Administrator'
            )
        ]
    # Should we indeed use -H here?
    else:
        return ['sudo', '-H']


def ensure_dir_exists(d):
    if not os.path.exists(d):
        os.makedirs(d)


def create_file(fname):
    ensure_dir_exists(os.path.dirname(os.path.abspath(fname)))
    with open(fname, 'a'):
        os.utime(fname, times=None)


def copy_path(path, d):
    if os.path.isdir(path):
        shutil.copytree(
            path,
            os.path.join(d, basepath(path)),
            copy_function=shutil.copy
        )
    else:
        shutil.copy(path, d)


def remove_path(path):
    try:
        shutil.rmtree(path)
    except (FileNotFoundError, OSError):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def basepath(path):
    return os.path.basename(os.path.normpath(path))


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
    old_evars = {}

    for ev in evars:
        if ev in os.environ:
            old_evars[ev] = os.environ[ev]
        os.environ[ev] = evars[ev]

    try:
        yield
    finally:
        for ev in evars:
            if ev in old_evars:
                os.environ[ev] = old_evars[ev]
            else:
                os.environ.pop(ev)


@contextmanager
def temp_move_path(path, d):
    if os.path.exists(path):
        dst = shutil.move(path, d)

        try:
            yield dst
        finally:
            os.replace(dst, path)
    else:
        yield
