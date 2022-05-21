import sys

import pytest
from packaging.requirements import Requirement

from hatch.venv.core import TempVirtualEnv
from hatchling.dep.core import dependencies_in_sync


def test_no_dependencies(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        assert dependencies_in_sync([], venv.sys_path)


def test_dependency_not_found(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        assert not dependencies_in_sync([Requirement('binary')], venv.sys_path)


@pytest.mark.requires_internet
def test_dependency_found(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(['pip', 'install', 'binary'], check=True, capture_output=True)
        assert dependencies_in_sync([Requirement('binary')], venv.sys_path)


@pytest.mark.requires_internet
def test_version_unmet(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(['pip', 'install', 'binary'], check=True, capture_output=True)
        assert not dependencies_in_sync([Requirement('binary>9000')], venv.sys_path)


def test_marker_met(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        assert dependencies_in_sync([Requirement('binary; python_version < "1"')], venv.sys_path)


def test_marker_unmet(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        assert not dependencies_in_sync([Requirement('binary; python_version > "1"')], venv.sys_path)


@pytest.mark.requires_internet
def test_extra_no_dependencies(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(['pip', 'install', 'binary'], check=True, capture_output=True)
        assert not dependencies_in_sync([Requirement('binary[foo]')], venv.sys_path)


@pytest.mark.requires_internet
def test_unknown_extra(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(['pip', 'install', 'requests[security]==2.25.1'], check=True, capture_output=True)
        assert not dependencies_in_sync([Requirement('requests[foo]')], venv.sys_path)


@pytest.mark.requires_internet
def test_extra_unmet(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(['pip', 'install', 'requests==2.25.1'], check=True, capture_output=True)
        assert not dependencies_in_sync([Requirement('requests[security]==2.25.1')], venv.sys_path)


@pytest.mark.requires_internet
def test_extra_met(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(['pip', 'install', 'requests[security]==2.25.1'], check=True, capture_output=True)
        assert dependencies_in_sync([Requirement('requests[security]==2.25.1')], venv.sys_path)
