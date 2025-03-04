import sys

import pytest
from packaging.requirements import Requirement

from hatch.venv.core import TempUVVirtualEnv, TempVirtualEnv
from hatchling.dep.core import dependencies_in_sync


def test_no_dependencies(platform):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        assert dependencies_in_sync([], venv.sys_path)


def test_dependency_not_found(platform):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        assert not dependencies_in_sync([Requirement('binary')], venv.sys_path)


@pytest.mark.requires_internet
def test_dependency_found(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, 'pip', 'install', 'binary'], check=True, capture_output=True)
        assert dependencies_in_sync([Requirement('binary')], venv.sys_path)


@pytest.mark.requires_internet
def test_version_unmet(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, 'pip', 'install', 'binary'], check=True, capture_output=True)
        assert not dependencies_in_sync([Requirement('binary>9000')], venv.sys_path)


def test_marker_met(platform):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        assert dependencies_in_sync([Requirement('binary; python_version < "1"')], venv.sys_path)


def test_marker_unmet(platform):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        assert not dependencies_in_sync([Requirement('binary; python_version > "1"')], venv.sys_path)


@pytest.mark.requires_internet
def test_extra_no_dependencies(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, 'pip', 'install', 'binary'], check=True, capture_output=True)
        assert not dependencies_in_sync([Requirement('binary[foo]')], venv.sys_path)


@pytest.mark.requires_internet
def test_unknown_extra(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            [uv_on_path, 'pip', 'install', 'requests[security]==2.25.1'], check=True, capture_output=True
        )
        assert not dependencies_in_sync([Requirement('requests[foo]')], venv.sys_path)


@pytest.mark.requires_internet
def test_extra_unmet(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, 'pip', 'install', 'requests==2.25.1'], check=True, capture_output=True)
        assert not dependencies_in_sync([Requirement('requests[security]==2.25.1')], venv.sys_path)


@pytest.mark.requires_internet
def test_extra_met(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            [uv_on_path, 'pip', 'install', 'requests[security]==2.25.1'], check=True, capture_output=True
        )
        assert dependencies_in_sync([Requirement('requests[security]==2.25.1')], venv.sys_path)


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_dependency_git_pip(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            ['pip', 'install', 'requests@git+https://github.com/psf/requests'], check=True, capture_output=True
        )
        assert dependencies_in_sync([Requirement('requests@git+https://github.com/psf/requests')], venv.sys_path)


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_dependency_git_uv(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            [uv_on_path, 'pip', 'install', 'requests@git+https://github.com/psf/requests'],
            check=True,
            capture_output=True,
        )
        assert dependencies_in_sync([Requirement('requests@git+https://github.com/psf/requests')], venv.sys_path)


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_dependency_git_revision_pip(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            ['pip', 'install', 'requests@git+https://github.com/psf/requests@main'], check=True, capture_output=True
        )
        assert dependencies_in_sync([Requirement('requests@git+https://github.com/psf/requests@main')], venv.sys_path)


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_dependency_git_revision_uv(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            [uv_on_path, 'pip', 'install', 'requests@git+https://github.com/psf/requests@main'],
            check=True,
            capture_output=True,
        )
        assert dependencies_in_sync([Requirement('requests@git+https://github.com/psf/requests@main')], venv.sys_path)


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_dependency_git_commit(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            [
                uv_on_path,
                'pip',
                'install',
                'requests@git+https://github.com/psf/requests@7f694b79e114c06fac5ec06019cada5a61e5570f',
            ],
            check=True,
            capture_output=True,
        )
        assert dependencies_in_sync(
            [Requirement('requests@git+https://github.com/psf/requests@7f694b79e114c06fac5ec06019cada5a61e5570f')],
            venv.sys_path,
        )
