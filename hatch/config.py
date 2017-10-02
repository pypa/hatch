import os
from functools import wraps

from appdirs import user_data_dir

from hatch.settings import load_settings

VENV_DIR_ISOLATED = os.path.join(user_data_dir('hatch', ''), 'venvs')
VENV_DIR_SHARED = os.path.expanduser(os.path.join('~', '.virtualenvs'))


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
