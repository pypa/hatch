from hatchling.build import build_editable, build_sdist, build_wheel


def test_sdist(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    project_config = project_path / 'pyproject.toml'
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

    build_path = project_path / 'dist'
    build_path.mkdir()

    with project_path.as_cwd():
        expected_artifact = build_sdist(str(build_path))

    build_artifacts = list(build_path.iterdir())
    assert len(build_artifacts) == 1
    assert expected_artifact == str(build_artifacts[0].name)
    assert expected_artifact.endswith('.tar.gz')


def test_wheel(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    project_config = project_path / 'pyproject.toml'
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

    build_path = project_path / 'dist'
    build_path.mkdir()

    with project_path.as_cwd():
        expected_artifact = build_wheel(str(build_path))

    build_artifacts = list(build_path.iterdir())
    assert len(build_artifacts) == 1
    assert expected_artifact == str(build_artifacts[0].name)
    assert expected_artifact.endswith('.whl')


def test_editable(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    project_config = project_path / 'pyproject.toml'
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

    build_path = project_path / 'dist'
    build_path.mkdir()

    with project_path.as_cwd():
        expected_artifact = build_editable(str(build_path), None)

    build_artifacts = list(build_path.iterdir())
    assert len(build_artifacts) == 1
    assert expected_artifact == str(build_artifacts[0].name)
    assert expected_artifact.endswith('.whl')
