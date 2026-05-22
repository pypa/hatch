import os
import re

import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.project.constants import DEFAULT_BUILD_SCRIPT, DEFAULT_CONFIG_FILE, BuildEnvVars
from hatch.project.core import Project

pytestmark = [pytest.mark.usefixtures("mock_backend_process")]


@pytest.mark.requires_internet
class TestOtherBackend:
    def test_standard(self, hatch, temp_dir, helpers):
        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / "my-app"
        data_path = temp_dir / "data"
        data_path.mkdir()

        project = Project(path)
        config = dict(project.raw_config)
        config["build-system"]["requires"] = ["flit-core"]
        config["build-system"]["build-backend"] = "flit_core.buildapi"
        config["project"]["version"] = "0.0.1"
        config["project"]["dynamic"] = []
        del config["project"]["license"]
        project.save_config(config)

        build_directory = path / "dist"
        assert not build_directory.is_dir()

        with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("build")
            assert result.exit_code == 0, result.output

        assert build_directory.is_dir()

        artifacts = list(build_directory.iterdir())
        assert len(artifacts) == 2

        wheel_path = build_directory / "my_app-0.0.1-py3-none-any.whl"
        assert wheel_path.is_file()

        sdist_path = build_directory / "my_app-0.0.1.tar.gz"
        assert sdist_path.is_file()

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            Creating environment: hatch-build
            Checking dependencies
            Syncing dependencies
            Inspecting build dependencies
            ──────────────────────────────────── sdist ─────────────────────────────────────
            {sdist_path.relative_to(path)}
            ──────────────────────────────────── wheel ─────────────────────────────────────
            {wheel_path.relative_to(path)}
            """
        )

        build_directory.remove()
        with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("build", "-t", "wheel")

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            Inspecting build dependencies
            ──────────────────────────────────── wheel ─────────────────────────────────────
            {wheel_path.relative_to(path)}
            """
        )

        assert build_directory.is_dir()
        assert wheel_path.is_file()
        assert not sdist_path.is_file()

        build_directory.remove()
        with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("build", "-t", "sdist")

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            Inspecting build dependencies
            ──────────────────────────────────── sdist ─────────────────────────────────────
            {sdist_path.relative_to(path)}
            """
        )

        assert build_directory.is_dir()
        assert not wheel_path.is_file()
        assert sdist_path.is_file()

    def test_legacy(self, hatch, temp_dir, helpers):
        path = temp_dir / "tmp"
        path.mkdir()
        data_path = temp_dir / "data"
        data_path.mkdir()

        (path / "pyproject.toml").write_text(
            """\
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
"""
        )
        (path / "setup.py").write_text(
            """\
import setuptools
setuptools.setup(name="tmp", version="0.0.1")
"""
        )
        (path / "tmp.py").write_text(
            """\
print("Hello World!")
"""
        )
        (path / "README.md").touch()

        build_directory = path / "dist"
        assert not build_directory.is_dir()

        with path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
            result = hatch("build")
            assert result.exit_code == 0, result.output

        assert build_directory.is_dir()

        artifacts = list(build_directory.iterdir())
        assert len(artifacts) == 2

        wheel_path = build_directory / "tmp-0.0.1-py3-none-any.whl"
        assert wheel_path.is_file()

        sdist_path = build_directory / "tmp-0.0.1.tar.gz"
        assert sdist_path.is_file()

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            Creating environment: hatch-build
            Checking dependencies
            Syncing dependencies
            Inspecting build dependencies
            ──────────────────────────────────── sdist ─────────────────────────────────────
            {sdist_path.relative_to(path)}
            ──────────────────────────────────── wheel ─────────────────────────────────────
            {wheel_path.relative_to(path)}
            """
        )


@pytest.mark.allow_backend_process
def test_incompatible_environment(hatch, temp_dir, helpers, build_env_config):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    project = Project(path)
    helpers.update_project_environment(project, "hatch-build", {"python": "9000", **build_env_config})

    with path.as_cwd():
        result = hatch("build")

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Environment `hatch-build` is incompatible: cannot locate Python: 9000
        """
    )


@pytest.mark.allow_backend_process
@pytest.mark.requires_internet
def test_no_compatibility_check_if_exists(hatch, temp_dir, helpers, mocker):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("build")
        assert result.exit_code == 0, result.output

    build_directory = project_path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        ──────────────────────────────────── wheel ─────────────────────────────────────
        """
    )

    build_directory.remove()
    mocker.patch("hatch.env.virtual.VirtualEnvironment.check_compatibility", side_effect=Exception("incompatible"))
    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("build")
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        ──────────────────────────────────── wheel ─────────────────────────────────────
        """
    )


@pytest.mark.requires_internet
def test_unknown_targets(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    with path.as_cwd():
        result = hatch("build", "-t", "foo")

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ───────────────────────────────────── foo ──────────────────────────────────────
        Unknown build targets: foo
        """
    )


@pytest.mark.requires_internet
def test_mutually_exclusive_hook_options(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    with path.as_cwd():
        result = hatch("build", "--hooks-only", "--no-hooks")

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        Cannot use both --hooks-only and --no-hooks together
        """
    )


@pytest.mark.requires_internet
def test_default(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    with path.as_cwd():
        result = hatch("build")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith(".tar.gz"))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

    assert result.output == helpers.dedent(
        f"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path.relative_to(path)}
        """
    )


@pytest.mark.requires_internet
def test_explicit_targets(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    with path.as_cwd():
        result = hatch("build", "-t", "wheel")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 1

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

    assert result.output == helpers.dedent(
        f"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path.relative_to(path)}
        """
    )


@pytest.mark.requires_internet
def test_explicit_directory(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    build_directory = temp_dir / "dist"

    with path.as_cwd():
        result = hatch("build", str(build_directory))

    assert result.exit_code == 0, result.output
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith(".tar.gz"))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

    assert result.output == helpers.dedent(
        f"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        {sdist_path}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path}
        """
    )


@pytest.mark.requires_internet
def test_explicit_directory_env_var(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"
    build_directory = temp_dir / "dist"

    with path.as_cwd({BuildEnvVars.LOCATION: str(build_directory)}):
        result = hatch("build")

    assert result.exit_code == 0, result.output
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith(".tar.gz"))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

    assert result.output == helpers.dedent(
        f"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        {sdist_path}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path}
        """
    )


@pytest.mark.requires_internet
def test_clean(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch("build")
        assert result.exit_code == 0, result.output

        result = hatch("version", "minor")
        assert result.exit_code == 0, result.output

        result = hatch("build")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()
    assert (path / "my_app" / "lib.so").is_file()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 4

    test_file = build_directory / "test.txt"
    test_file.touch()

    with path.as_cwd():
        result = hatch("version", "9000")
        assert result.exit_code == 0, result.output

        result = hatch("build", "-c")
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 3
    assert test_file in artifacts

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith(".tar.gz"))
    assert "9000" in str(sdist_path)

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))
    assert "9000" in str(wheel_path)

    assert result.output == helpers.dedent(
        f"""
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path.relative_to(path)}
        """
    )


@pytest.mark.requires_internet
def test_clean_env_var(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    with path.as_cwd():
        result = hatch("build")
        assert result.exit_code == 0, result.output

        result = hatch("version", "minor")
        assert result.exit_code == 0, result.output

        result = hatch("build")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 4

    test_file = build_directory / "test.txt"
    test_file.touch()

    with path.as_cwd({BuildEnvVars.CLEAN: "true"}):
        result = hatch("version", "9000")
        assert result.exit_code == 0, result.output

        result = hatch("build")
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 3
    assert test_file in artifacts

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith(".tar.gz"))
    assert "9000" in str(sdist_path)

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))
    assert "9000" in str(wheel_path)

    assert result.output == helpers.dedent(
        f"""
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path.relative_to(path)}
        """
    )


@pytest.mark.requires_internet
def test_clean_only(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch("build")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()
    build_artifact = path / "my_app" / "lib.so"
    assert build_artifact.is_file()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    with path.as_cwd():
        result = hatch("version", "minor")
        assert result.exit_code == 0, result.output

        result = hatch("build", "--clean-only")
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert not artifacts
    assert not build_artifact.exists()

    assert result.output == helpers.dedent(
        """
        Inspecting build dependencies
        """
    )


@pytest.mark.requires_internet
def test_clean_only_hooks_only(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch("build")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()
    build_artifact = path / "my_app" / "lib.so"
    assert build_artifact.is_file()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    with path.as_cwd():
        result = hatch("version", "minor")
        assert result.exit_code == 0, result.output

        result = hatch("build", "--clean-only", "--hooks-only")
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2
    assert not build_artifact.exists()

    assert result.output == helpers.dedent(
        """
        Inspecting build dependencies
        """
    )


@pytest.mark.requires_internet
def test_clean_hooks_after(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch("build", "--clean-hooks-after")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()
    build_artifact = path / "my_app" / "lib.so"
    assert not build_artifact.exists()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith(".tar.gz"))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

    assert result.output == helpers.dedent(
        f"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path.relative_to(path)}
        """
    )


@pytest.mark.requires_internet
def test_clean_hooks_after_env_var(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd({BuildEnvVars.CLEAN_HOOKS_AFTER: "true"}):
        result = hatch("build")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()
    build_artifact = path / "my_app" / "lib.so"
    assert not build_artifact.exists()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith(".tar.gz"))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

    assert result.output == helpers.dedent(
        f"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path.relative_to(path)}
        """
    )


@pytest.mark.requires_internet
def test_clean_only_no_hooks(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch("build")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()
    build_artifact = path / "my_app" / "lib.so"
    assert build_artifact.is_file()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    with path.as_cwd():
        result = hatch("version", "minor")
        assert result.exit_code == 0, result.output

        result = hatch("build", "--clean-only", "--no-hooks")
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert not artifacts
    assert build_artifact.is_file()

    assert result.output == helpers.dedent(
        """
        Inspecting build dependencies
        """
    )


@pytest.mark.requires_internet
def test_hooks_only(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch("-v", "build", "-t", "wheel", "--hooks-only")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 0
    assert (path / "my_app" / "lib.so").is_file()

    helpers.assert_output_match(
        result.output,
        r"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        cmd \[1\] \| python -u .+
        ──────────────────────────────────── wheel ─────────────────────────────────────
        cmd \[1\] \| python -u -m hatchling build --target wheel --hooks-only
        Building `wheel` version `standard`
        Only ran build hooks for `wheel` version `standard`
        """,
    )


@pytest.mark.requires_internet
def test_hooks_only_env_var(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd({BuildEnvVars.HOOKS_ONLY: "true"}):
        result = hatch("-v", "build", "-t", "wheel")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 0
    assert (path / "my_app" / "lib.so").is_file()

    helpers.assert_output_match(
        result.output,
        r"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        cmd \[1\] \| python -u .+
        ──────────────────────────────────── wheel ─────────────────────────────────────
        cmd \[1\] \| python -u -m hatchling build --target wheel --hooks-only
        Building `wheel` version `standard`
        Only ran build hooks for `wheel` version `standard`
        """,
    )


@pytest.mark.requires_internet
def test_extensions_only(hatch, temp_dir, helpers, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch("-v", "build", "--ext")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 0
    assert (path / "my_app" / "lib.so").is_file()

    helpers.assert_output_match(
        result.output,
        r"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        cmd \[1\] \| python -u .+
        ──────────────────────────────────── wheel ─────────────────────────────────────
        cmd \[1\] \| python -u -m hatchling build --target wheel --hooks-only
        Building `wheel` version `standard`
        Only ran build hooks for `wheel` version `standard`
        """,
    )


@pytest.mark.requires_internet
def test_no_hooks(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch("build", "-t", "wheel", "--no-hooks")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 1
    assert not (path / "my_app" / "lib.so").exists()

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

    assert result.output == helpers.dedent(
        f"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path.relative_to(path)}
        """
    )


@pytest.mark.requires_internet
def test_no_hooks_env_var(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {"hooks": {"custom": {"path": build_script.name}}}
    project.save_config(config)

    with path.as_cwd({BuildEnvVars.NO_HOOKS: "true"}):
        result = hatch("build", "-t", "wheel")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 1
    assert not (path / "my_app" / "lib.so").exists()

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

    assert result.output == helpers.dedent(
        f"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path.relative_to(path)}
        """
    )


@pytest.mark.requires_internet
def test_debug_verbosity(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    with path.as_cwd():
        result = hatch("-v", "build", "-t", "wheel:standard")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 1

    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

    helpers.assert_output_match(
        result.output,
        rf"""
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── wheel ─────────────────────────────────────
        cmd \[1\] \| python -u -m hatchling build --target wheel:standard
        Building `wheel` version `standard`
        {re.escape(str(wheel_path.relative_to(path)))}
        """,
    )


@pytest.mark.allow_backend_process
@pytest.mark.requires_internet
def test_shipped(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("build")
        assert result.exit_code == 0, result.output

    env_data_path = data_path / "env" / "virtual"
    assert env_data_path.is_dir()

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == "hatch-build"

    build_directory = project_path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        ──────────────────────────────────── wheel ─────────────────────────────────────
        """
    )

    # Test removal while we're here
    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("env", "remove", "hatch-build")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Removing environment: hatch-build
        """
    )

    assert not storage_path.is_dir()


@pytest.mark.allow_backend_process
@pytest.mark.requires_internet
def test_build_dependencies(hatch, temp_dir, helpers):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    data_path = temp_dir / "data"
    data_path.mkdir()

    build_script = project_path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            import binary
            from hatchling.builders.wheel import WheelBuilder

            def get_builder():
                return CustomWheelBuilder

            class CustomWheelBuilder(WheelBuilder):
                def build(self, **kwargs):
                    pathlib.Path('test.txt').write_text(str(binary.convert_units(1024)))
                    yield from super().build(**kwargs)
            """
        )
    )

    project = Project(project_path)
    config = dict(project.raw_config)
    config["tool"]["hatch"]["build"] = {
        "targets": {"custom": {"dependencies": ["binary"], "path": DEFAULT_BUILD_SCRIPT}},
    }
    project.save_config(config)

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch("build", "-t", "custom")
        assert result.exit_code == 0, result.output

    build_directory = project_path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 1

    output_file = project_path / "test.txt"
    assert output_file.is_file()

    assert str(output_file.read_text()) == "(1.0, 'KiB')"

    assert result.output == helpers.dedent(
        """
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        Syncing dependencies
        ──────────────────────────────────── custom ────────────────────────────────────
        """
    )


@pytest.mark.requires_internet
def test_plugin_dependencies_unmet(hatch, temp_dir, helpers, mock_plugin_installation):
    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / "my-app"

    dependency = os.urandom(16).hex()
    (path / DEFAULT_CONFIG_FILE).write_text(
        helpers.dedent(
            f"""
            [env]
            requires = ["{dependency}"]
            """
        )
    )

    with path.as_cwd():
        result = hatch("build")
        assert result.exit_code == 0, result.output

    build_directory = path / "dist"
    assert build_directory.is_dir()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith(".tar.gz"))
    wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

    assert result.output == helpers.dedent(
        f"""
        Syncing environment plugin requirements
        Creating environment: hatch-build
        Checking dependencies
        Syncing dependencies
        Inspecting build dependencies
        ──────────────────────────────────── sdist ─────────────────────────────────────
        {sdist_path.relative_to(path)}
        ──────────────────────────────────── wheel ─────────────────────────────────────
        {wheel_path.relative_to(path)}
        """
    )
    helpers.assert_plugin_installation(mock_plugin_installation, [dependency])


@pytest.mark.requires_internet
class TestBuildAllFlag:
    """Tests for the --all / -a flag on the build command."""

    def test_all_flag_accepted(self, hatch, temp_dir):
        """Verify --all flag is accepted and does not error with 'unknown option'."""
        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / "my-app"

        with path.as_cwd():
            result = hatch("build", "--all")
            assert result.exit_code == 0, result.output

        # With no workspace members configured, --all falls back to single-project build
        build_directory = path / "dist"
        assert build_directory.is_dir()

        artifacts = list(build_directory.iterdir())
        assert len(artifacts) == 2

    def test_short_flag_accepted(self, hatch, temp_dir):
        """Verify -a short form is accepted and does not error with 'unknown option'."""
        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / "my-app"

        with path.as_cwd():
            result = hatch("build", "-a")
            assert result.exit_code == 0, result.output

        # With no workspace members configured, -a falls back to single-project build
        build_directory = path / "dist"
        assert build_directory.is_dir()

        artifacts = list(build_directory.iterdir())
        assert len(artifacts) == 2

    def test_backward_compatibility_without_all(self, hatch, temp_dir, helpers):
        """Verify existing build behavior is unchanged without --all flag."""
        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / "my-app"

        with path.as_cwd():
            result = hatch("build")
            assert result.exit_code == 0, result.output

        build_directory = path / "dist"
        assert build_directory.is_dir()

        artifacts = list(build_directory.iterdir())
        assert len(artifacts) == 2

        sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith(".tar.gz"))
        wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

        assert result.output == helpers.dedent(
            f"""
            Creating environment: hatch-build
            Checking dependencies
            Syncing dependencies
            Inspecting build dependencies
            ──────────────────────────────────── sdist ─────────────────────────────────────
            {sdist_path.relative_to(path)}
            ──────────────────────────────────── wheel ─────────────────────────────────────
            {wheel_path.relative_to(path)}
            """
        )

    def test_mutually_exclusive_hook_options_with_all(self, hatch, temp_dir):
        """Verify --hooks-only + --no-hooks conflict is detected early with --all."""
        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / "my-app"

        with path.as_cwd():
            result = hatch("build", "--all", "--hooks-only", "--no-hooks")

        assert result.exit_code == 1, result.output
        assert "Cannot use both --hooks-only and --no-hooks options together" in result.output


@pytest.mark.requires_internet
class TestBuildAllWorkspace:
    """Integration tests for building all workspace members with --all."""

    def test_multi_package_workspace(self, hatch, temp_dir, helpers):
        """Test end-to-end build of a multi-package workspace with --all."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        # Create workspace root pyproject.toml
        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "workspace-root"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*"]

                [tool.hatch.build.targets.wheel]
                packages = ["workspace_root"]
                """
            )
        )

        workspace_pkg = workspace_root / "workspace_root"
        workspace_pkg.mkdir()
        (workspace_pkg / "__init__.py").write_text('__version__ = "0.1.0"')

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        # Create member-a
        member_a_dir = packages_dir / "member-a"
        member_a_dir.mkdir()
        (member_a_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-a"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_a"]
                """
            )
        )
        src_a = member_a_dir / "member_a"
        src_a.mkdir()
        (src_a / "__init__.py").write_text('__version__ = "0.1.0"')

        # Create member-b
        member_b_dir = packages_dir / "member-b"
        member_b_dir.mkdir()
        (member_b_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-b"
                version = "0.2.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_b"]
                """
            )
        )
        src_b = member_b_dir / "member_b"
        src_b.mkdir()
        (src_b / "__init__.py").write_text('__version__ = "0.2.0"')

        with workspace_root.as_cwd():
            result = hatch("build", "--all")

        assert result.exit_code == 0, result.output

        dist_dir = workspace_root / "dist"
        assert dist_dir.is_dir()
        artifacts = list(dist_dir.iterdir())
        assert len(artifacts) == 6
        assert any(a.name.endswith(".whl") and "workspace_root" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "workspace_root" in a.name for a in artifacts)
        assert any(a.name.endswith(".whl") and "member_a" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "member_a" in a.name for a in artifacts)
        assert any(a.name.endswith(".whl") and "member_b" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "member_b" in a.name for a in artifacts)

        assert "workspace-root" in result.output
        assert "member-a" in result.output
        assert "member-b" in result.output

    def test_shared_location(self, hatch, temp_dir, helpers):
        """Test --all with a shared location argument (all artifacts in one directory)."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "workspace-root"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*"]

                [tool.hatch.build.targets.wheel]
                packages = ["workspace_root"]
                """
            )
        )

        workspace_pkg = workspace_root / "workspace_root"
        workspace_pkg.mkdir()
        (workspace_pkg / "__init__.py").write_text('__version__ = "0.1.0"')

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        # Create member-a
        member_a_dir = packages_dir / "member-a"
        member_a_dir.mkdir()
        (member_a_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-a"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_a"]
                """
            )
        )
        src_a = member_a_dir / "member_a"
        src_a.mkdir()
        (src_a / "__init__.py").write_text('__version__ = "0.1.0"')

        # Create member-b
        member_b_dir = packages_dir / "member-b"
        member_b_dir.mkdir()
        (member_b_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-b"
                version = "0.2.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_b"]
                """
            )
        )
        src_b = member_b_dir / "member_b"
        src_b.mkdir()
        (src_b / "__init__.py").write_text('__version__ = "0.2.0"')

        shared_dist = temp_dir / "dist"

        with workspace_root.as_cwd():
            result = hatch("build", "--all", str(shared_dist))

        assert result.exit_code == 0, result.output

        assert shared_dist.is_dir()
        artifacts = list(shared_dist.iterdir())
        assert len(artifacts) == 6
        assert any(a.name.endswith(".whl") and "workspace_root" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "workspace_root" in a.name for a in artifacts)
        assert any(a.name.endswith(".whl") and "member_a" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "member_a" in a.name for a in artifacts)
        assert any(a.name.endswith(".whl") and "member_b" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "member_b" in a.name for a in artifacts)

    def test_fail_fast_on_build_error(self, hatch, temp_dir, helpers):
        """Test --all where one member has a build error (fail-fast behavior)."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "workspace-root"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*"]

                [tool.hatch.build.targets.wheel]
                packages = ["workspace_root"]
                """
            )
        )

        workspace_pkg = workspace_root / "workspace_root"
        workspace_pkg.mkdir()
        (workspace_pkg / "__init__.py").write_text('__version__ = "0.1.0"')

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        # Create member-a (valid, will build first alphabetically)
        member_a_dir = packages_dir / "member-a"
        member_a_dir.mkdir()
        (member_a_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-a"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_a"]
                """
            )
        )
        src_a = member_a_dir / "member_a"
        src_a.mkdir()
        (src_a / "__init__.py").write_text('__version__ = "0.1.0"')

        # Create member-b (will fail to build - uses a build hook that exits with error)
        member_b_dir = packages_dir / "member-b"
        member_b_dir.mkdir()
        (member_b_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-b"
                version = "0.2.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_b"]

                [tool.hatch.build.hooks.custom]
                path = "hatch_build.py"
                """
            )
        )
        src_b = member_b_dir / "member_b"
        src_b.mkdir()
        (src_b / "__init__.py").write_text('__version__ = "0.2.0"')
        (member_b_dir / "hatch_build.py").write_text(
            helpers.dedent(
                """
                import sys
                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        sys.exit("Intentional build failure")
                """
            )
        )

        with workspace_root.as_cwd():
            result = hatch("build", "--all")

        assert result.exit_code == 1, result.output

        dist_dir = workspace_root / "dist"
        assert not dist_dir.is_dir()

    def test_target_wheel_only(self, hatch, temp_dir, helpers):
        """Test --all with --target wheel only."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "workspace-root"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*"]

                [tool.hatch.build.targets.wheel]
                packages = ["workspace_root"]
                """
            )
        )

        workspace_pkg = workspace_root / "workspace_root"
        workspace_pkg.mkdir()
        (workspace_pkg / "__init__.py").write_text('__version__ = "0.1.0"')

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        # Create member-a
        member_a_dir = packages_dir / "member-a"
        member_a_dir.mkdir()
        (member_a_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-a"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_a"]
                """
            )
        )
        src_a = member_a_dir / "member_a"
        src_a.mkdir()
        (src_a / "__init__.py").write_text('__version__ = "0.1.0"')

        with workspace_root.as_cwd():
            result = hatch("build", "--all", "-t", "wheel")

        assert result.exit_code == 0, result.output

        dist_dir = workspace_root / "dist"
        assert dist_dir.is_dir()
        artifacts = list(dist_dir.iterdir())
        assert len(artifacts) == 2
        assert all(a.name.endswith(".whl") for a in artifacts)

    def test_non_buildable_root(self, hatch, temp_dir, helpers):
        """Test --all from a workspace root that has no [project] section."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*"]
                """
            )
        )

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        # Create member-a
        member_a_dir = packages_dir / "member-a"
        member_a_dir.mkdir()
        (member_a_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-a"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_a"]
                """
            )
        )
        src_a = member_a_dir / "member_a"
        src_a.mkdir()
        (src_a / "__init__.py").write_text('__version__ = "0.1.0"')

        with workspace_root.as_cwd():
            result = hatch("build", "--all")

        assert result.exit_code == 0, result.output

        dist_dir = workspace_root / "dist"
        assert dist_dir.is_dir()
        artifacts = list(dist_dir.iterdir())
        assert len(artifacts) == 2
        assert any(a.name.endswith(".whl") and "member_a" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "member_a" in a.name for a in artifacts)

    def test_relative_paths_in_member(self, hatch, temp_dir, helpers):
        """Test --all where a member's pyproject.toml uses relative paths."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "workspace-root"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*"]

                [tool.hatch.build.targets.wheel]
                packages = ["workspace_root"]
                """
            )
        )

        workspace_pkg = workspace_root / "workspace_root"
        workspace_pkg.mkdir()
        (workspace_pkg / "__init__.py").write_text('__version__ = "0.1.0"')

        # Create a shared README at workspace root
        (workspace_root / "README.md").write_text("# Shared README\n\nThis is a shared readme file.")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        # Create member-a with a relative path to the shared README
        member_a_dir = packages_dir / "member-a"
        member_a_dir.mkdir()
        (member_a_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-a"
                version = "0.1.0"
                readme = "../../README.md"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_a"]
                """
            )
        )
        src_a = member_a_dir / "member_a"
        src_a.mkdir()
        (src_a / "__init__.py").write_text('__version__ = "0.1.0"')

        with workspace_root.as_cwd():
            result = hatch("build", "--all")

        assert result.exit_code == 0, result.output

        dist_dir = workspace_root / "dist"
        assert dist_dir.is_dir()
        artifacts = list(dist_dir.iterdir())
        assert len(artifacts) == 4
        assert any(a.name.endswith(".whl") and "member_a" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "member_a" in a.name for a in artifacts)

    def test_fallback_no_workspace_members(self, hatch, temp_dir, helpers):
        """Test fallback behavior: --all with no workspace members configured."""
        project_name = "My.App"

        with temp_dir.as_cwd():
            result = hatch("new", project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / "my-app"

        with path.as_cwd():
            result = hatch("build", "--all")

        assert result.exit_code == 0, result.output

        # Should fall back to single-project build
        build_directory = path / "dist"
        assert build_directory.is_dir()

        artifacts = list(build_directory.iterdir())
        assert len(artifacts) == 2

        sdist_path = next(artifact for artifact in artifacts if artifact.name.endswith(".tar.gz"))
        wheel_path = next(artifact for artifact in artifacts if artifact.name.endswith(".whl"))

        assert result.output == helpers.dedent(
            f"""
            Creating environment: hatch-build
            Checking dependencies
            Syncing dependencies
            Inspecting build dependencies
            ──────────────────────────────────── sdist ─────────────────────────────────────
            {sdist_path.relative_to(path)}
            ──────────────────────────────────── wheel ─────────────────────────────────────
            {wheel_path.relative_to(path)}
            """
        )

    def test_deduplication_overlapping_patterns(self, hatch, temp_dir, helpers):
        """Test deduplication: overlapping glob patterns resolve to unique builds."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "workspace-root"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*", "packages/member-a"]

                [tool.hatch.build.targets.wheel]
                packages = ["workspace_root"]
                """
            )
        )

        workspace_pkg = workspace_root / "workspace_root"
        workspace_pkg.mkdir()
        (workspace_pkg / "__init__.py").write_text('__version__ = "0.1.0"')

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        # Create member-a (will be matched by both patterns)
        member_a_dir = packages_dir / "member-a"
        member_a_dir.mkdir()
        (member_a_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-a"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_a"]
                """
            )
        )
        src_a = member_a_dir / "member_a"
        src_a.mkdir()
        (src_a / "__init__.py").write_text('__version__ = "0.1.0"')

        with workspace_root.as_cwd(), pytest.raises(ValueError, match="duplicate"):
            hatch("build", "--all")


@pytest.mark.requires_internet
class TestBuildAllMonorepoNoBuildableRoot:
    """Integration tests for --all with a monorepo that has no top-level [project] table."""

    def test_multi_member_monorepo(self, hatch, temp_dir, helpers):
        """Test building multiple workspace members from a non-buildable root."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*"]
                """
            )
        )

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        member_a_dir = packages_dir / "member-a"
        member_a_dir.mkdir()
        (member_a_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-a"
                version = "1.0.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_a"]
                """
            )
        )
        src_a = member_a_dir / "member_a"
        src_a.mkdir()
        (src_a / "__init__.py").write_text('__version__ = "1.0.0"')

        member_b_dir = packages_dir / "member-b"
        member_b_dir.mkdir()
        (member_b_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "member-b"
                version = "2.0.0"
                dependencies = ["member-a"]

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["member_b"]
                """
            )
        )
        src_b = member_b_dir / "member_b"
        src_b.mkdir()
        (src_b / "__init__.py").write_text('__version__ = "2.0.0"')

        with workspace_root.as_cwd():
            result = hatch("build", "--all")

        assert result.exit_code == 0, result.output

        dist_dir = workspace_root / "dist"
        assert dist_dir.is_dir()
        artifacts = list(dist_dir.iterdir())
        assert len(artifacts) == 4
        assert any(a.name.endswith(".whl") and "member_a" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "member_a" in a.name for a in artifacts)
        assert any(a.name.endswith(".whl") and "member_b" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "member_b" in a.name for a in artifacts)

        assert "member-a" in result.output
        assert "member-b" in result.output

    def test_shared_location_argument(self, hatch, temp_dir, helpers):
        """Test --all with explicit output directory from a non-buildable root."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*"]
                """
            )
        )

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        member_dir = packages_dir / "my-lib"
        member_dir.mkdir()
        (member_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "my-lib"
                version = "0.5.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["my_lib"]
                """
            )
        )
        src = member_dir / "my_lib"
        src.mkdir()
        (src / "__init__.py").write_text('__version__ = "0.5.0"')

        output_dir = temp_dir / "output"

        with workspace_root.as_cwd():
            result = hatch("build", "--all", str(output_dir))

        assert result.exit_code == 0, result.output

        assert output_dir.is_dir()
        artifacts = list(output_dir.iterdir())
        assert len(artifacts) == 2
        assert any(a.name.endswith(".whl") and "my_lib" in a.name for a in artifacts)
        assert any(a.name.endswith(".tar.gz") and "my_lib" in a.name for a in artifacts)

    def test_wheel_only(self, hatch, temp_dir, helpers):
        """Test --all -t wheel from a non-buildable root."""
        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*"]
                """
            )
        )

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        for name in ("alpha", "beta"):
            member_dir = packages_dir / name
            member_dir.mkdir()
            (member_dir / "pyproject.toml").write_text(
                helpers.dedent(
                    f"""
                    [project]
                    name = "{name}"
                    version = "0.1.0"

                    [build-system]
                    requires = ["hatchling"]
                    build-backend = "hatchling.build"

                    [tool.hatch.build.targets.wheel]
                    packages = ["{name}"]
                    """
                )
            )
            src = member_dir / name
            src.mkdir()
            (src / "__init__.py").write_text('__version__ = "0.1.0"')

        with workspace_root.as_cwd():
            result = hatch("build", "--all", "-t", "wheel")

        assert result.exit_code == 0, result.output

        dist_dir = workspace_root / "dist"
        assert dist_dir.is_dir()
        artifacts = list(dist_dir.iterdir())
        assert len(artifacts) == 2
        assert all(a.name.endswith(".whl") for a in artifacts)
        assert any("alpha" in a.name for a in artifacts)
        assert any("beta" in a.name for a in artifacts)

    def test_sdist_excludes_unrelated_workspace_files(self, hatch, temp_dir, helpers):
        """Test that member sdists only contain their own files, not workspace-level directories."""
        import tarfile

        workspace_root = temp_dir / "workspace"
        workspace_root.mkdir()

        (workspace_root / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [tool.hatch.envs.hatch-build]
                workspace.members = ["packages/*"]
                """
            )
        )

        # Create workspace-level directories that should NOT appear in member sdists
        docs_dir = workspace_root / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.md").write_text("# Documentation")
        (docs_dir / "guide.md").write_text("# Guide")

        scripts_dir = workspace_root / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "deploy.sh").write_text("#!/bin/bash\necho deploy")

        (workspace_root / "README.md").write_text("# Workspace Root README")

        packages_dir = workspace_root / "packages"
        packages_dir.mkdir()

        member_dir = packages_dir / "my-lib"
        member_dir.mkdir()
        (member_dir / "pyproject.toml").write_text(
            helpers.dedent(
                """
                [project]
                name = "my-lib"
                version = "0.1.0"

                [build-system]
                requires = ["hatchling"]
                build-backend = "hatchling.build"

                [tool.hatch.build.targets.wheel]
                packages = ["my_lib"]
                """
            )
        )
        (member_dir / "README.md").write_text("# my-lib")
        src = member_dir / "my_lib"
        src.mkdir()
        (src / "__init__.py").write_text('__version__ = "0.1.0"')
        (src / "core.py").write_text("def hello(): return 'hello'")

        with workspace_root.as_cwd():
            result = hatch("build", "--all")

        assert result.exit_code == 0, result.output

        dist_dir = workspace_root / "dist"
        assert dist_dir.is_dir()

        sdist_path = next(a for a in dist_dir.iterdir() if a.name.endswith(".tar.gz"))

        with tarfile.open(str(sdist_path), "r:gz") as tar:
            names = tar.getnames()

        assert any("my_lib/__init__.py" in n for n in names)
        assert any("my_lib/core.py" in n for n in names)
        assert any("pyproject.toml" in n for n in names)

        assert not any("docs/" in n for n in names)
        assert not any("docs/index.md" in n for n in names)
        assert not any("scripts/" in n for n in names)
        assert not any("deploy.sh" in n for n in names)
        assert not any("packages/" in n for n in names)
