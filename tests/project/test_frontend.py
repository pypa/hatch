import json
import sys

import pytest

from hatch.env.plugin.interface import EnvironmentInterface
from hatch.project.core import Project
from hatchling.builders.constants import EDITABLES_REQUIREMENT
from hatchling.metadata.spec import project_metadata_from_core_metadata

BACKENDS = [("hatchling", "hatchling.build"), ("flit-core", "flit_core.buildapi")]


class MockEnvironment(EnvironmentInterface):  # no cov
    PLUGIN_NAME = "mock"

    def find(self):
        pass

    def create(self):
        pass

    def remove(self):
        pass

    def exists(self):
        pass

    def install_project(self):
        pass

    def install_project_dev_mode(self):
        pass

    def dependencies_in_sync(self):
        pass

    def sync_dependencies(self):
        pass


class TestPrepareMetadata:
    @pytest.mark.parametrize(
        ("backend_pkg", "backend_api"),
        [pytest.param(backend_pkg, backend_api, id=backend_pkg) for backend_pkg, backend_api in BACKENDS],
    )
    def test_wheel(self, temp_dir, temp_dir_data, platform, global_application, backend_pkg, backend_api):
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            f"""\
[build-system]
requires = ["{backend_pkg}"]
build-backend = "{backend_api}"

[project]
name = "foo"
version = "9000.42"
description = "text"
"""
        )

        package_dir = project_dir / "foo"
        package_dir.mkdir()
        (package_dir / "__init__.py").touch()

        project = Project(project_dir)
        project.build_env = MockEnvironment(
            temp_dir,
            project.metadata,
            "default",
            project.config.envs["default"],
            {},
            temp_dir_data,
            temp_dir_data,
            platform,
            0,
            global_application,
        )

        output_dir = temp_dir / "output"
        output_dir.mkdir()
        script = project.build_frontend.scripts.prepare_metadata(
            output_dir=str(output_dir), project_root=str(project_dir)
        )
        platform.check_command([sys.executable, "-c", script])
        work_dir = output_dir / "work"
        output = json.loads((output_dir / "output.json").read_text())
        metadata_file = work_dir / output["return_val"] / "METADATA"

        assert project_metadata_from_core_metadata(metadata_file.read_text()) == {
            "name": "foo",
            "version": "9000.42",
            "description": "text",
        }

    @pytest.mark.parametrize(
        ("backend_pkg", "backend_api"),
        [pytest.param(backend_pkg, backend_api, id=backend_pkg) for backend_pkg, backend_api in BACKENDS],
    )
    def test_editable(self, temp_dir, temp_dir_data, platform, global_application, backend_pkg, backend_api):
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            f"""\
[build-system]
requires = ["{backend_pkg}"]
build-backend = "{backend_api}"

[project]
name = "foo"
version = "9000.42"
description = "text"
"""
        )

        package_dir = project_dir / "foo"
        package_dir.mkdir()
        (package_dir / "__init__.py").touch()

        project = Project(project_dir)
        project.build_env = MockEnvironment(
            temp_dir,
            project.metadata,
            "default",
            project.config.envs["default"],
            {},
            temp_dir_data,
            temp_dir_data,
            platform,
            0,
            global_application,
        )

        output_dir = temp_dir / "output"
        output_dir.mkdir()
        script = project.build_frontend.scripts.prepare_metadata(
            output_dir=str(output_dir), project_root=str(project_dir), editable=True
        )
        platform.check_command([sys.executable, "-c", script])
        work_dir = output_dir / "work"
        output = json.loads((output_dir / "output.json").read_text())
        metadata_file = work_dir / output["return_val"] / "METADATA"

        assert project_metadata_from_core_metadata(metadata_file.read_text()) == {
            "name": "foo",
            "version": "9000.42",
            "description": "text",
        }


class TestBuildWheel:
    @pytest.mark.parametrize(
        ("backend_pkg", "backend_api"),
        [pytest.param(backend_pkg, backend_api, id=backend_pkg) for backend_pkg, backend_api in BACKENDS],
    )
    def test_standard(self, temp_dir, temp_dir_data, platform, global_application, backend_pkg, backend_api):
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            f"""\
[build-system]
requires = ["{backend_pkg}"]
build-backend = "{backend_api}"

[project]
name = "foo"
version = "9000.42"
description = "text"
"""
        )

        package_dir = project_dir / "foo"
        package_dir.mkdir()
        (package_dir / "__init__.py").touch()

        project = Project(project_dir)
        project.build_env = MockEnvironment(
            temp_dir,
            project.metadata,
            "default",
            project.config.envs["default"],
            {},
            temp_dir_data,
            temp_dir_data,
            platform,
            0,
            global_application,
        )

        output_dir = temp_dir / "output"
        output_dir.mkdir()
        script = project.build_frontend.scripts.build_wheel(output_dir=str(output_dir), project_root=str(project_dir))
        platform.check_command([sys.executable, "-c", script])
        work_dir = output_dir / "work"
        output = json.loads((output_dir / "output.json").read_text())
        wheel_path = work_dir / output["return_val"]

        assert wheel_path.is_file()
        assert wheel_path.name.startswith("foo-9000.42-")
        assert wheel_path.name.endswith(".whl")

    @pytest.mark.parametrize(
        ("backend_pkg", "backend_api"),
        [pytest.param(backend_pkg, backend_api, id=backend_pkg) for backend_pkg, backend_api in BACKENDS],
    )
    def test_editable(self, temp_dir, temp_dir_data, platform, global_application, backend_pkg, backend_api):
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            f"""\
[build-system]
requires = ["{backend_pkg}"]
build-backend = "{backend_api}"

[project]
name = "foo"
version = "9000.42"
description = "text"
"""
        )

        package_dir = project_dir / "foo"
        package_dir.mkdir()
        (package_dir / "__init__.py").touch()

        project = Project(project_dir)
        project.build_env = MockEnvironment(
            temp_dir,
            project.metadata,
            "default",
            project.config.envs["default"],
            {},
            temp_dir_data,
            temp_dir_data,
            platform,
            0,
            global_application,
        )

        output_dir = temp_dir / "output"
        output_dir.mkdir()
        script = project.build_frontend.scripts.build_wheel(
            output_dir=str(output_dir), project_root=str(project_dir), editable=True
        )
        platform.check_command([sys.executable, "-c", script])
        work_dir = output_dir / "work"
        output = json.loads((output_dir / "output.json").read_text())
        wheel_path = work_dir / output["return_val"]

        assert wheel_path.is_file()
        assert wheel_path.name.startswith("foo-9000.42-")
        assert wheel_path.name.endswith(".whl")


class TestSourceDistribution:
    @pytest.mark.parametrize(
        ("backend_pkg", "backend_api"),
        [pytest.param(backend_pkg, backend_api, id=backend_pkg) for backend_pkg, backend_api in BACKENDS],
    )
    def test_standard(self, temp_dir, temp_dir_data, platform, global_application, backend_pkg, backend_api):
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            f"""\
[build-system]
requires = ["{backend_pkg}"]
build-backend = "{backend_api}"

[project]
name = "foo"
version = "9000.42"
description = "text"
"""
        )

        package_dir = project_dir / "foo"
        package_dir.mkdir()
        (package_dir / "__init__.py").touch()

        project = Project(project_dir)
        project.build_env = MockEnvironment(
            temp_dir,
            project.metadata,
            "default",
            project.config.envs["default"],
            {},
            temp_dir_data,
            temp_dir_data,
            platform,
            0,
            global_application,
        )

        output_dir = temp_dir / "output"
        output_dir.mkdir()
        script = project.build_frontend.scripts.build_sdist(output_dir=str(output_dir), project_root=str(project_dir))
        platform.check_command([sys.executable, "-c", script])
        work_dir = output_dir / "work"
        output = json.loads((output_dir / "output.json").read_text())
        sdist_path = work_dir / output["return_val"]

        assert sdist_path.is_file()
        assert sdist_path.name == "foo-9000.42.tar.gz"


class TestGetRequires:
    @pytest.mark.parametrize(
        ("backend_pkg", "backend_api"),
        [pytest.param(backend_pkg, backend_api, id=backend_pkg) for backend_pkg, backend_api in BACKENDS],
    )
    @pytest.mark.parametrize("build", ["sdist", "wheel", "editable"])
    def test_default(self, temp_dir, temp_dir_data, platform, global_application, backend_pkg, backend_api, build):
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            f"""\
[build-system]
requires = ["{backend_pkg}"]
build-backend = "{backend_api}"

[project]
name = "foo"
version = "9000.42"
description = "text"
"""
        )

        package_dir = project_dir / "foo"
        package_dir.mkdir()
        (package_dir / "__init__.py").touch()

        project = Project(project_dir)
        project.build_env = MockEnvironment(
            temp_dir,
            project.metadata,
            "default",
            project.config.envs["default"],
            {},
            temp_dir_data,
            temp_dir_data,
            platform,
            0,
            global_application,
        )

        output_dir = temp_dir / "output"
        output_dir.mkdir()
        script = project.build_frontend.scripts.get_requires(
            output_dir=str(output_dir), project_root=str(project_dir), build=build
        )
        platform.check_command([sys.executable, "-c", script])
        output = json.loads((output_dir / "output.json").read_text())

        assert output["return_val"] == (
            [EDITABLES_REQUIREMENT] if backend_pkg == "hatchling" and build == "editable" else []
        )


class TestHatchGetBuildDeps:
    def test_default(self, temp_dir, temp_dir_data, platform, global_application):
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            """\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "foo"
version = "9000.42"
"""
        )

        package_dir = project_dir / "foo"
        package_dir.mkdir()
        (package_dir / "__init__.py").touch()

        project = Project(project_dir)
        project.build_env = MockEnvironment(
            temp_dir,
            project.metadata,
            "default",
            project.config.envs["default"],
            {},
            temp_dir_data,
            temp_dir_data,
            platform,
            0,
            global_application,
        )

        output_dir = temp_dir / "output"
        output_dir.mkdir()
        script = project.build_frontend.hatch.scripts.get_build_deps(
            output_dir=str(output_dir), project_root=str(project_dir), targets=["sdist", "wheel"]
        )
        platform.check_command([sys.executable, "-c", script])
        output = json.loads((output_dir / "output.json").read_text())

        assert output == []
