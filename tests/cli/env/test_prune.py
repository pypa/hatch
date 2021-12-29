from hatch.config.constants import AppEnvVars, ConfigEnvVars
from hatch.project.core import Project


def test_unknown_type(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    cache_path = temp_dir / 'cache'
    cache_path.mkdir()

    project = Project(project_path)
    config = dict(project.config.envs['default'])
    config['type'] = 'foo'
    helpers.update_project_environment(project, 'default', config)

    with project_path.as_cwd(env_vars={ConfigEnvVars.CACHE: str(cache_path)}):
        result = hatch('env', 'prune')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Environment `default` has unknown type: foo
        """
    )


def test_all(hatch, helpers, temp_dir, config_file):
    project_name = 'My App'

    cache_path = temp_dir / 'cache'
    config_file.model.dirs.env = str(cache_path)
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'foo', {})
    helpers.update_project_environment(project, 'bar', {})

    with project_path.as_cwd():
        result = hatch('env', 'create', 'foo')

    assert result.exit_code == 0, result.output

    with project_path.as_cwd():
        result = hatch('env', 'create', 'bar')

    assert result.exit_code == 0, result.output

    env_cache_path = cache_path / 'env' / 'virtual'
    assert env_cache_path.is_dir()

    storage_dirs = list(env_cache_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 2

    with project_path.as_cwd():
        result = hatch('env', 'prune')

    assert result.exit_code == 0, result.output
    assert not result.output

    assert not storage_path.is_dir()


def test_incompatible_ok(hatch, helpers, temp_dir, config_file):
    project_name = 'My App'

    cache_path = temp_dir / 'cache'
    config_file.model.dirs.env = str(cache_path)
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    helpers.update_project_environment(
        project, 'default', {'skip-install': True, 'platforms': ['foo'], **project.config.envs['default']}
    )

    with project_path.as_cwd():
        result = hatch('env', 'prune')

    assert result.exit_code == 0, result.output
    assert not result.output


def test_active(hatch, temp_dir, helpers, config_file):
    project_name = 'My App'

    cache_path = temp_dir / 'cache'
    config_file.model.dirs.env = str(cache_path)
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    with project_path.as_cwd(env_vars={AppEnvVars.ENV_ACTIVE: 'default'}):
        result = hatch('env', 'prune')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Cannot remove active environment: default
        """
    )
