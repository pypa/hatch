import os
import shutil

import pytest

from hatch.env import get_python_path
from hatch.utils import temp_chdir
from hatch.venv import create_venv, venv


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


def test_levels():
    with temp_chdir() as d:
        d1 = os.path.join(d, 'test_env1')
        d2 = os.path.join(d, 'test_env2')
        d3 = os.path.join(d, 'test_env3')
        create_venv(d1)
        create_venv(d2)
        create_venv(d3)

        with venv(d1):
            assert os.environ.get('_HATCH_LEVEL_') == '1'
            with venv(d2):
                assert os.environ.get('_HATCH_LEVEL_') == '2'
                with venv(d3):
                    assert os.environ.get('_HATCH_LEVEL_') == '3'
                assert os.environ.get('_HATCH_LEVEL_') == '2'
            assert os.environ.get('_HATCH_LEVEL_') == '1'
