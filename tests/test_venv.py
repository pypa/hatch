import os
import shutil

import pytest

from hatch.venv import create_venv, venv
from hatch.utils import get_python_path
from .utils import temp_chdir


def test_default():
    with temp_chdir() as d:
        d = os.path.join(d, 'test_env')
        create_venv(d)

        assert os.path.exists(d)


def test_pypath():
    with temp_chdir() as d:
        d = os.path.join(d, 'test_env')
        create_venv(d, pypath=get_python_path())

        assert os.path.exists(d)


def test_venv():
    with temp_chdir() as d:
        d = os.path.join(d, 'test_env')
        create_venv(d)
        global_python = get_python_path()

        with venv(d):
            venv_python = get_python_path()

        assert global_python != venv_python
        assert global_python == get_python_path()


def test_venv_unknown():
    with temp_chdir() as d:
        d = os.path.join(d, 'test_env')
        create_venv(d)

        with pytest.raises(OSError):
            if os.path.exists(os.path.join(d, 'bin')):  # no cov
                shutil.rmtree(os.path.join(d, 'bin'))
            if os.path.exists(os.path.join(d, 'Scripts')):  # no cov
                shutil.rmtree(os.path.join(d, 'Scripts'))
            with venv(d):  # no cov
                pass
