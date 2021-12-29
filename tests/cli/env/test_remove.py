from hatch.config.constants import AppEnvVars
from hatch.project.core import Project


def test_unknown(hatch, temp_dir, helpers, config_file):
    project_name = 'My App'

    cache_path = temp_dir / 'cache'
    config_file.model.dirs.env = str(cache_path)
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    with project_path.as_cwd():
        result = hatch('env', 'remove', 'foo')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Unknown environment: foo
        """
    )


def test_nonexistent(hatch, temp_dir, config_file):
    project_name = 'My App'

    cache_path = temp_dir / 'cache'
    config_file.model.dirs.env = str(cache_path)
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    with project_path.as_cwd():
        result = hatch('env', 'remove', 'default')

    assert result.exit_code == 0, result.output
    assert not result.output


def test_single(hatch, helpers, temp_dir, config_file):
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

    foo_env_path = storage_path / 'foo'
    bar_env_path = storage_path / 'bar'

    assert foo_env_path.is_dir()
    assert bar_env_path.is_dir()

    with project_path.as_cwd():
        result = hatch('env', 'remove', 'bar')

    assert result.exit_code == 0, result.output
    assert not result.output

    assert foo_env_path.is_dir()
    assert not bar_env_path.is_dir()


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

    foo_env_path = storage_path / 'foo'
    bar_env_path = storage_path / 'bar'

    assert foo_env_path.is_dir()
    assert bar_env_path.is_dir()

    with project_path.as_cwd():
        result = hatch('env', 'remove', 'foo')

    assert result.exit_code == 0, result.output
    assert not result.output

    with project_path.as_cwd():
        result = hatch('env', 'remove', 'bar')

    assert result.exit_code == 0, result.output
    assert not result.output

    assert not storage_path.is_dir()


def test_matrix_all(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'foo', {'matrix': [{'version': ['9000', '42']}]})

    with project_path.as_cwd():
        result = hatch('env', 'create', 'foo')

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

    foo_env_path = storage_path / 'foo.42'
    bar_env_path = storage_path / 'foo.9000'

    assert foo_env_path.is_dir()
    assert bar_env_path.is_dir()

    with project_path.as_cwd():
        result = hatch('env', 'remove', 'foo')

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
        result = hatch('env', 'remove')

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
        result = hatch('env', 'remove')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Cannot remove active environment: default
        """
    )


def test_active_override(hatch, helpers, temp_dir, config_file):
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

    with project_path.as_cwd():
        result = hatch('env', 'create')

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
    assert len(env_dirs) == 1

    (storage_path / 'default').is_dir()

    with project_path.as_cwd(env_vars={AppEnvVars.ENV_ACTIVE: 'foo'}):
        result = hatch('env', 'remove', 'default')

    assert result.exit_code == 0, result.output
    assert not result.output

    assert not storage_path.is_dir()
