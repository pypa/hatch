import json
import zipfile

import pytest

from hatchling.build import build_editable, build_sdist, build_wheel, get_requires_for_build_wheel


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


def create_variant_project(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins["default"]["src-layout"] = False
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch("new", "My.App")

    assert result.exit_code == 0, result.output

    project_path = temp_dir / "my-app"
    (project_path / "pyproject.toml").write_text(
        helpers.dedent(
            """
            [project]
            name = 'my__app'
            dynamic = [ 'version' ]

            [tool.hatch.version]
            path = 'my_app/__about__.py'

            [variant.default-priorities]
            namespace = ['stub']

            [variant.providers.stub]
            requires = ['stub-variant-provider']
            plugin-api = 'stub_variant_provider'

            [variant.variants.foo]
            stub.level = ['v3']
            """
        )
    )
    return project_path


class TestWheelVariants:
    def test_no_variant_without_label(self, hatch, helpers, temp_dir, config_file):
        project_path = create_variant_project(hatch, helpers, temp_dir, config_file)
        build_path = project_path / "dist"
        build_path.mkdir()

        with project_path.as_cwd():
            expected_artifact = build_wheel(str(build_path), {})

        assert expected_artifact.endswith("-none-any.whl")
        with zipfile.ZipFile(str(build_path / expected_artifact), "r") as zip_archive:
            assert not any(name.endswith("/variant.json") for name in zip_archive.namelist())

    @pytest.mark.parametrize("label", ["null", ["null"]], ids=["string", "list"])
    def test_null_variant(self, hatch, helpers, temp_dir, config_file, label):
        project_path = create_variant_project(hatch, helpers, temp_dir, config_file)
        build_path = project_path / "dist"
        build_path.mkdir()

        with project_path.as_cwd():
            expected_artifact = build_wheel(str(build_path), {"variant-label": label})

        assert expected_artifact.endswith("-none-any-null.whl")
        with zipfile.ZipFile(str(build_path / expected_artifact), "r") as zip_archive:
            variant_json = next(name for name in zip_archive.namelist() if name.endswith("/variant.json"))
            assert json.loads(zip_archive.read(variant_json))["variants"] == {"null": {}}

    def test_label_specified_multiple_times(self, hatch, helpers, temp_dir, config_file):
        project_path = create_variant_project(hatch, helpers, temp_dir, config_file)

        with project_path.as_cwd(), pytest.raises(ValueError, match="must be specified exactly once"):
            build_wheel(str(project_path / "dist"), {"variant-label": ["foo", "null"]})

    def test_requires_for_build_wheel(self, hatch, helpers, temp_dir, config_file):
        project_path = create_variant_project(hatch, helpers, temp_dir, config_file)

        with project_path.as_cwd():
            assert get_requires_for_build_wheel(None) == []
            assert get_requires_for_build_wheel({"variant-label": "null"}) == []
            assert get_requires_for_build_wheel({"variant-label": "foo"}) == ["stub-variant-provider"]

            with pytest.raises(ValueError, match="Variant `bar` is not defined"):
                get_requires_for_build_wheel({"variant-label": "bar"})

    def test_prepare_metadata_for_build_wheel(self, hatch, helpers, temp_dir, config_file):
        import hatchling.build

        prepare_metadata = getattr(hatchling.build, "prepare_metadata_for_build_wheel", None)
        if prepare_metadata is None:  # no cov
            pytest.skip("prepare_metadata_for_build_wheel is not exposed when a pip build tracker is active")

        project_path = create_variant_project(hatch, helpers, temp_dir, config_file)
        metadata_path = project_path / "metadata"
        metadata_path.mkdir()

        with project_path.as_cwd():
            plain_directory = metadata_path / prepare_metadata(str(metadata_path), None)
            assert not (plain_directory / "variant.json").is_file()

            variant_directory = metadata_path / prepare_metadata(str(metadata_path), {"variant-label": "null"})
            assert json.loads((variant_directory / "variant.json").read_text())["variants"] == {"null": {}}
