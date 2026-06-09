import os
import sys

import pytest

from hatch.dep.core import Dependency
from hatch.dep.sync import InstalledDistributions
from hatch.venv.core import TempUVVirtualEnv, TempVirtualEnv


def test_no_dependencies(platform):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([])


def test_dependency_not_found(platform):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert not distributions.dependencies_in_sync([Dependency("binary")])


@pytest.mark.requires_internet
def test_dependency_found(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, "pip", "install", "binary"], check=True, capture_output=True)
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([Dependency("binary")])


@pytest.mark.requires_internet
def test_version_unmet(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, "pip", "install", "binary"], check=True, capture_output=True)
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert not distributions.dependencies_in_sync([Dependency("binary>9000")])


def test_marker_met(platform):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([Dependency('binary; python_version < "1"')])


def test_marker_unmet(platform):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert not distributions.dependencies_in_sync([Dependency('binary; python_version > "1"')])


@pytest.mark.requires_internet
def test_extra_no_dependencies(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, "pip", "install", "binary"], check=True, capture_output=True)
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert not distributions.dependencies_in_sync([Dependency("binary[foo]")])


@pytest.mark.requires_internet
def test_unknown_extra(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            [uv_on_path, "pip", "install", "requests[security]==2.25.1"], check=True, capture_output=True
        )
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert not distributions.dependencies_in_sync([Dependency("requests[foo]")])


@pytest.mark.requires_internet
def test_extra_unmet(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, "pip", "install", "requests==2.25.1"], check=True, capture_output=True)
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert not distributions.dependencies_in_sync([Dependency("requests[security]==2.25.1")])


@pytest.mark.requires_internet
def test_extra_met(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            [uv_on_path, "pip", "install", "requests[security]==2.25.1"], check=True, capture_output=True
        )
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([Dependency("requests[security]==2.25.1")])


@pytest.mark.requires_internet
def test_local_dir(hatch, temp_dir, platform, uv_on_path):
    project_name = os.urandom(10).hex()

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    project_path = temp_dir / project_name
    dependency_string = f"{project_name}@{project_path.as_uri()}"
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, "pip", "install", str(project_path)], check=True, capture_output=True)
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([Dependency(dependency_string)])


@pytest.mark.requires_internet
def test_local_dir_editable(hatch, temp_dir, platform, uv_on_path):
    project_name = os.urandom(10).hex()

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    project_path = temp_dir / project_name
    dependency_string = f"{project_name}@{project_path.as_uri()}"
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, "pip", "install", "-e", str(project_path)], check=True, capture_output=True)
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([Dependency(dependency_string, editable=True)])


@pytest.mark.requires_internet
def test_local_dir_editable_mismatch(hatch, temp_dir, platform, uv_on_path):
    project_name = os.urandom(10).hex()

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    project_path = temp_dir / project_name
    dependency_string = f"{project_name}@{project_path.as_uri()}"
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command([uv_on_path, "pip", "install", "-e", str(project_path)], check=True, capture_output=True)
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert not distributions.dependencies_in_sync([Dependency(dependency_string)])


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_dependency_git_pip(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            ["pip", "install", "requests@git+https://github.com/psf/requests"], check=True, capture_output=True
        )
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([Dependency("requests@git+https://github.com/psf/requests")])


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_dependency_git_uv(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            [uv_on_path, "pip", "install", "requests@git+https://github.com/psf/requests"],
            check=True,
            capture_output=True,
        )
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([Dependency("requests@git+https://github.com/psf/requests")])


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_dependency_git_revision_pip(platform):
    with TempVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            ["pip", "install", "requests@git+https://github.com/psf/requests@main"], check=True, capture_output=True
        )
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([Dependency("requests@git+https://github.com/psf/requests@main")])


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_dependency_git_revision_uv(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            [uv_on_path, "pip", "install", "requests@git+https://github.com/psf/requests@main"],
            check=True,
            capture_output=True,
        )
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([Dependency("requests@git+https://github.com/psf/requests@main")])


@pytest.mark.requires_internet
@pytest.mark.requires_git
def test_dependency_git_commit(platform, uv_on_path):
    with TempUVVirtualEnv(sys.executable, platform) as venv:
        platform.run_command(
            [
                uv_on_path,
                "pip",
                "install",
                "requests@git+https://github.com/psf/requests@7f694b79e114c06fac5ec06019cada5a61e5570f",
            ],
            check=True,
            capture_output=True,
        )
        distributions = InstalledDistributions(sys_path=venv.sys_path)
        assert distributions.dependencies_in_sync([
            Dependency("requests@git+https://github.com/psf/requests@7f694b79e114c06fac5ec06019cada5a61e5570f")
        ])


def test_dependency_path_with_unresolved_context_variable():
    """
    Regression test: Dependency.path should raise ValueError for unresolved context variables.
    Context variables must be resolved before creating Dependency objects.
    """
    unformatted_dep_string = "my-package @ {root:parent:uri}/my-package"
    dep = Dependency(unformatted_dep_string)

    with pytest.raises(ValueError, match="invalid scheme"):
        _ = dep.path


def test_dependency_path_with_special_characters():
    """
    Regression test: Dependency.path should handle URL-encoded special characters.
    Paths with special characters like '+' get URL-encoded to '%2B' in URIs,
    and should be decoded back when accessing the path property.
    """
    # Create a dependency with a path containing URL-encoded special character
    # Simulating what happens when a path with '+' is converted via .as_uri()
    dep_string = "my-package @ file:///tmp/my%2Bproject"
    dep = Dependency(dep_string)

    # The path property should decode %2B back to +
    assert dep.path is not None
    assert "my+project" in str(dep.path)
