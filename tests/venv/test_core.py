import json
import os
import sys

import pytest

from hatch.utils.structures import EnvVars
from hatch.venv.core import VirtualEnv


def test_initialization_does_not_create(temp_dir, platform):
    venv_dir = temp_dir / 'venv'
    venv = VirtualEnv(venv_dir, platform)

    assert not venv.exists()

    with pytest.raises(OSError, match='Unable to locate executables directory'):
        _ = venv.executables_directory


def test_remove_non_existent_no_error(temp_dir, platform):
    venv_dir = temp_dir / 'venv'
    venv = VirtualEnv(venv_dir, platform)
    venv.remove()


def test_creation(temp_dir, platform):
    venv_dir = temp_dir / 'venv'
    venv = VirtualEnv(venv_dir, platform)
    venv.create(sys.executable)

    assert venv_dir.is_dir()
    assert venv.exists()


def test_executables_directory(temp_dir, platform):
    venv_dir = temp_dir / 'venv'
    venv = VirtualEnv(venv_dir, platform)
    venv.create(sys.executable)

    assert venv.executables_directory.is_dir()
    for entry in venv.executables_directory.iterdir():
        if entry.name.startswith('py'):
            break
    else:  # no cov
        raise AssertionError('Unable to locate Python executable')


def test_activation(temp_dir, platform):
    venv_dir = temp_dir / 'venv'
    venv = VirtualEnv(venv_dir, platform)
    venv.create(sys.executable)

    with EnvVars(exclude=VirtualEnv.IGNORED_ENV_VARS):
        os.environ['PATH'] = str(temp_dir)
        os.environ['VIRTUAL_ENV'] = 'foo'
        for env_var in VirtualEnv.IGNORED_ENV_VARS:
            os.environ[env_var] = 'foo'

        venv.activate()

        assert os.environ['PATH'] == f'{venv.executables_directory}{os.pathsep}{temp_dir}'
        assert os.environ['VIRTUAL_ENV'] == str(venv_dir)
        for env_var in VirtualEnv.IGNORED_ENV_VARS:
            assert env_var not in os.environ

        venv.deactivate()

        assert os.environ['PATH'] == str(temp_dir)
        assert os.environ['VIRTUAL_ENV'] == 'foo'
        for env_var in VirtualEnv.IGNORED_ENV_VARS:
            assert os.environ[env_var] == 'foo'


def test_activation_path_env_var_missing(temp_dir, platform):
    venv_dir = temp_dir / 'venv'
    venv = VirtualEnv(venv_dir, platform)
    venv.create(sys.executable)

    with EnvVars(exclude=VirtualEnv.IGNORED_ENV_VARS):
        os.environ.pop('PATH', None)
        os.environ['VIRTUAL_ENV'] = 'foo'
        for env_var in VirtualEnv.IGNORED_ENV_VARS:
            os.environ[env_var] = 'foo'

        venv.activate()

        assert os.environ['PATH'] == str(venv.executables_directory)
        assert os.environ['VIRTUAL_ENV'] == str(venv_dir)
        for env_var in VirtualEnv.IGNORED_ENV_VARS:
            assert env_var not in os.environ

        venv.deactivate()

        assert 'PATH' not in os.environ
        assert os.environ['VIRTUAL_ENV'] == 'foo'
        for env_var in VirtualEnv.IGNORED_ENV_VARS:
            assert os.environ[env_var] == 'foo'


def test_context_manager(temp_dir, platform):
    venv_dir = temp_dir / 'venv'
    venv = VirtualEnv(venv_dir, platform)
    venv.create(sys.executable)

    with EnvVars(exclude=VirtualEnv.IGNORED_ENV_VARS):
        os.environ['PATH'] = str(temp_dir)
        os.environ['VIRTUAL_ENV'] = 'foo'
        for env_var in VirtualEnv.IGNORED_ENV_VARS:
            os.environ[env_var] = 'foo'

        with venv:
            assert os.environ['PATH'] == f'{venv.executables_directory}{os.pathsep}{temp_dir}'
            assert os.environ['VIRTUAL_ENV'] == str(venv_dir)
            for env_var in VirtualEnv.IGNORED_ENV_VARS:
                assert env_var not in os.environ

            # Run here while we have cleanup
            output = platform.run_command(['pip', 'freeze'], check=True, capture_output=True).stdout.decode('utf-8')
            assert output.strip().count('==') == 0

        assert os.environ['PATH'] == str(temp_dir)
        assert os.environ['VIRTUAL_ENV'] == 'foo'
        for env_var in VirtualEnv.IGNORED_ENV_VARS:
            assert os.environ[env_var] == 'foo'


def test_creation_allow_system_packages(temp_dir, platform):
    venv_dir = temp_dir / 'venv'
    venv = VirtualEnv(venv_dir, platform)
    venv.create(sys.executable, allow_system_packages=True)

    with venv:
        output = platform.run_command(['pip', 'freeze'], check=True, capture_output=True).stdout.decode('utf-8')

        assert output.strip().count('==') > 0


def test_sys_path(temp_dir, platform):
    venv_dir = temp_dir / 'venv'
    venv = VirtualEnv(venv_dir, platform)
    venv.create(sys.executable)

    with venv:
        output = platform.run_command(
            ['python', '-c', 'import json,sys;print(json.dumps([path for path in sys.path if path]))'],
            check=True,
            capture_output=True,
        ).stdout.decode('utf-8')

        assert venv.sys_path == venv.sys_path == json.loads(output)
