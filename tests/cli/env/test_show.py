from hatch.project.core import Project


def test_default(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    with project_path.as_cwd():
        result = hatch('env', 'show')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        default
        """
    )


def test_single_only(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, 'foo', {})
    helpers.update_project_environment(project, 'bar', {})

    with project_path.as_cwd():
        result = hatch('env', 'show')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        default
        foo
        bar
        """
    )


def test_single_and_matrix(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, 'foo', {'matrix': [{'version': ['9000', '3.14'], 'py': ['39', '310']}]})

    with project_path.as_cwd():
        result = hatch('env', 'show')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        default

        [foo]
        py39-9000
        py39-3.14
        py310-9000
        py310-3.14
        """
    )


def test_default_matrix_only(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project, 'default', {'matrix': [{'version': ['9000', '3.14'], 'py': ['39', '310']}]}
    )

    with project_path.as_cwd():
        result = hatch('env', 'show')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        py39-9000
        py39-3.14
        py310-9000
        py310-3.14
        """
    )


def test_all_matrix_types_with_single(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project, 'default', {'matrix': [{'version': ['9000', '3.14'], 'py': ['39', '310']}]}
    )
    helpers.update_project_environment(project, 'foo', {'matrix': [{'version': ['9000', '3.14'], 'py': ['39', '310']}]})
    helpers.update_project_environment(project, 'bar', {})

    with project_path.as_cwd():
        result = hatch('env', 'show')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        bar

        py39-9000
        py39-3.14
        py310-9000
        py310-3.14

        [foo]
        py39-9000
        py39-3.14
        py310-9000
        py310-3.14
        """
    )
