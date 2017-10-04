import os
from functools import wraps

from appdirs import user_data_dir

from hatch.settings import load_settings
from hatch.utils import ON_WINDOWS, venv_active

PYTHON_DIR_ISOLATED = os.path.join(user_data_dir('hatch', ''), 'pythons')
PYTHON_DIR_SHARED = os.path.expanduser(os.path.join('~', '.pythons'))
VENV_DIR_ISOLATED = os.path.join(user_data_dir('hatch', ''), 'venvs')
VENV_DIR_SHARED = os.path.expanduser(os.path.join('~', '.virtualenvs'))


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
        default_pip = os.environ.get('_DEFAULT_PIP_', None)
        if default_pip:
            return default_pip
        elif not ON_WINDOWS:
            return 'pip3'
    return 'pip'


def __get_python_dir_cache(f):  # no cov
    cached_python_dir = None

    @wraps(f)
    def wrapper(cached=True, reset=False):
        nonlocal cached_python_dir

        if not cached or not cached_python_dir or reset:
            python_dir = os.environ.get('_PYTHON_DIR_') or load_settings(lazy=True).get('python_dir')
            if python_dir:  # no cov
                if python_dir == 'isolated':
                    python_dir = PYTHON_DIR_ISOLATED
                elif python_dir == 'shared':
                    python_dir = PYTHON_DIR_SHARED
            else:  # no cov
                python_dir = PYTHON_DIR_SHARED

            cached_python_dir = python_dir

        return cached_python_dir

    return wrapper


@__get_python_dir_cache
def get_python_dir():
    pass  # no cov


def __get_venv_dir_cache(f):
    cached_venv_dir = None

    @wraps(f)
    def wrapper(cached=True, reset=False):
        nonlocal cached_venv_dir

        if not cached or not cached_venv_dir or reset:
            venv_dir = os.environ.get('_VENV_DIR_') or load_settings(lazy=True).get('venv_dir')
            if venv_dir:  # no cov
                if venv_dir == 'isolated':
                    venv_dir = VENV_DIR_ISOLATED
                elif venv_dir == 'shared':
                    venv_dir = VENV_DIR_SHARED
            else:  # no cov
                venv_dir = VENV_DIR_SHARED

            cached_venv_dir = venv_dir

        return cached_venv_dir

    return wrapper


@__get_venv_dir_cache
def get_venv_dir():
    pass  # no cov
