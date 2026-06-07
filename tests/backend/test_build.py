from hatchling.build import build_editable, build_sdist, build_wheel, get_requires_for_build_wheel
from hatchling.builders.constants import EDITABLES_REQUIREMENT


def test_sdist(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    project_config = project_path / "pyproject.toml"
    project_config.write_text(
        helpers.dedent(
            """
            [project]
            name = 'my__app'
            dynamic = [ 'version' ]

            [tool.hatch.version]
            path = 'my_app/__about__.py'

            [tool.hatch.build.targets.sdist]
            versions = '9000'
            """
        )
    )

    build_path = project_path / "dist"
    build_path.mkdir()

    with project_path.as_cwd():
        expected_artifact = build_sdist(str(build_path))

    build_artifacts = list(build_path.iterdir())
    assert len(build_artifacts) == 1
    assert expected_artifact == str(build_artifacts[0].name)
    assert expected_artifact.endswith(".tar.gz")


def test_wheel(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    project_config = project_path / "pyproject.toml"
    project_config.write_text(
        helpers.dedent(
            """
            [project]
            name = 'my__app'
            dynamic = [ 'version' ]

            [tool.hatch.version]
            path = 'my_app/__about__.py'

            [tool.hatch.build.targets.wheel]
            versions = '9000'
            """
        )
    )

    build_path = project_path / "dist"
    build_path.mkdir()

    with project_path.as_cwd():
        expected_artifact = build_wheel(str(build_path))

    build_artifacts = list(build_path.iterdir())
    assert len(build_artifacts) == 1
    assert expected_artifact == str(build_artifacts[0].name)
    assert expected_artifact.endswith(".whl")


def test_wheel_requires_editables_when_editable_version_selected(helpers, temp_dir):
    project_path = temp_dir / "project"
    package_dir = project_path / "src" / "demo_pkg"
    package_dir.ensure_dir_exists()
    package_dir.joinpath("__init__.py").touch()
    project_path.joinpath("pyproject.toml").write_text(
        helpers.dedent(
            """
            [project]
            name = "demo-pkg"
            version = "0.1.0"

            [tool.hatch.build.targets.wheel]
            packages = ["src/demo_pkg"]
            versions = ["editable"]
            """
        )
    )

    with project_path.as_cwd():
        assert get_requires_for_build_wheel(None) == [EDITABLES_REQUIREMENT]


def test_wheel_editable_version_with_dev_mode_dirs_does_not_require_editables(helpers, temp_dir):
    project_path = temp_dir / "project"
    package_dir = project_path / "src" / "demo_pkg"
    package_dir.ensure_dir_exists()
    package_dir.joinpath("__init__.py").touch()
    project_path.joinpath("pyproject.toml").write_text(
        helpers.dedent(
            """
            [project]
            name = "demo-pkg"
            version = "0.1.0"

            [tool.hatch.build.targets.wheel]
            packages = ["src/demo_pkg"]
            versions = ["editable"]
            dev-mode-dirs = ["src"]
            """
        )
    )

    with project_path.as_cwd():
        assert get_requires_for_build_wheel(None) == []


def test_editable(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    project_config = project_path / "pyproject.toml"
    project_config.write_text(
        helpers.dedent(
            """
            [project]
            name = 'my__app'
            dynamic = [ 'version' ]

            [tool.hatch.version]
            path = 'my_app/__about__.py'

            [tool.hatch.build.targets.wheel]
            versions = '9000'
            """
        )
    )

    build_path = project_path / "dist"
    build_path.mkdir()

    with project_path.as_cwd():
        expected_artifact = build_editable(str(build_path), None)

    build_artifacts = list(build_path.iterdir())
    assert len(build_artifacts) == 1
    assert expected_artifact == str(build_artifacts[0].name)
    assert expected_artifact.endswith(".whl")
