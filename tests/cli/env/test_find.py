from hatch.project.core import Project


def test_undefined(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    with project_path.as_cwd():
        result = hatch('env', 'find', 'test')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Environment `test` is not defined by project config
        """
    )


def test_single(hatch, helpers, temp_dir_data, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir_data.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir_data / 'my-app'

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})

    with project_path.as_cwd():
        result = hatch('env', 'create')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        Checking dependencies
        """
    )

    env_data_path = temp_dir_data / 'data' / 'env' / 'virtual'
    assert env_data_path.is_dir()

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    env_path = storage_path / 'my-app'

    with project_path.as_cwd():
        result = hatch('env', 'find')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {env_path}
        """
    )


def test_matrix(hatch, helpers, temp_dir_data, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir_data.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir_data / 'my-app'

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(
        project,
        'test',
        {
            'matrix': [{'version': ['9000', '42']}],
            'overrides': {'matrix': {'version': {'platforms': [{'value': 'foo', 'if': ['9000']}]}}},
        },
    )

    with project_path.as_cwd():
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test.42
        Checking dependencies
        Skipped 1 incompatible environment:
        test.9000 -> unsupported platform
        """
    )

    env_data_path = temp_dir_data / 'data' / 'env' / 'virtual'
    assert env_data_path.is_dir()

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    env_path = storage_path / 'test.42'

    with project_path.as_cwd():
        result = hatch('env', 'find', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {env_path}
        """
    )
