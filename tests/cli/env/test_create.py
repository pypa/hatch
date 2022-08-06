import pytest

from hatch.config.constants import AppEnvVars, ConfigEnvVars
from hatch.project.core import Project
from hatch.utils.structures import EnvVars
from hatch.venv.core import VirtualEnv


def test_undefined(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Environment `test` is not defined by project config
        """
    )


def test_unknown_type(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    config = dict(project.config.envs['default'])
    config['type'] = 'foo'
    helpers.update_project_environment(project, 'default', config)
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Environment `test` has unknown type: foo
        """
    )


def test_new(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Checking dependencies
        """
    )

    project = Project(project_path)
    assert project.config.envs == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'type': 'virtual', 'skip-install': True},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {},
    }

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'


def test_new_selected_python(hatch, helpers, temp_dir, config_file, python_on_path, mocker):
    mocker.patch('sys.executable')

    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path), AppEnvVars.PYTHON: python_on_path}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Checking dependencies
        """
    )

    project = Project(project_path)
    assert project.config.envs == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'type': 'virtual', 'skip-install': True},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {},
    }

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'


def test_selected_absolute_directory(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.model.dirs.env = {'virtual': '$VENVS_DIR'}
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    env_data_path = temp_dir / '.venvs'

    project = Project(project_path)
    assert project.config.envs == {'default': {'type': 'virtual'}}
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd({'VENVS_DIR': str(env_data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Checking dependencies
        """
    )

    project = Project(project_path)
    assert project.config.envs == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'type': 'virtual', 'skip-install': True},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {},
    }

    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'


def test_env_var_absolute_directory(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.model.dirs.env = {'virtual': '$VENVS_DIR'}
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    env_data_path = temp_dir / '.venvs'
    env_path = temp_dir / 'foo'

    project = Project(project_path)
    assert project.config.envs == {'default': {'type': 'virtual'}}
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd({'VENVS_DIR': str(env_data_path), 'HATCH_ENV_TYPE_VIRTUAL_PATH': str(env_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Checking dependencies
        """
    )

    project = Project(project_path)
    assert project.config.envs == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'type': 'virtual', 'skip-install': True},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {},
    }

    assert not env_data_path.is_dir()
    assert env_path.is_dir()


def test_selected_local_directory(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.model.dirs.env = {'virtual': '$VENVS_DIR'}
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    assert project.config.envs == {'default': {'type': 'virtual'}}
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd({'VENVS_DIR': '.venvs'}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Checking dependencies
        """
    )

    project = Project(project_path)
    assert project.config.envs == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'type': 'virtual', 'skip-install': True},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {},
    }

    env_data_path = project_path / '.venvs'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'


def test_env_var_local_directory(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.model.dirs.env = {'virtual': '$VENVS_DIR'}
    config_file.save()

    project_name = 'My.App'
    env_data_path = temp_dir / '.venvs'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    assert project.config.envs == {'default': {'type': 'virtual'}}
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd({'VENVS_DIR': str(env_data_path), 'HATCH_ENV_TYPE_VIRTUAL_PATH': '.venv'}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Checking dependencies
        """
    )

    project = Project(project_path)
    assert project.config.envs == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'type': 'virtual', 'skip-install': True},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {},
    }
    assert not env_data_path.is_dir()
    assert (project_path / '.venv').is_dir()


def test_enter_project_directory(hatch, config_file, helpers, temp_dir):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = 'foo'
    config_file.model.mode = 'project'
    config_file.model.project = project
    config_file.model.projects = {project: str(project_path)}
    config_file.save()

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {})

    with EnvVars({ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Checking dependencies
        """
    )

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'


def test_already_created(hatch, config_file, helpers, temp_dir):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Checking dependencies
        """
    )

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Environment `test` already exists
        """
    )


def test_default(hatch, config_file, helpers, temp_dir):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        Checking dependencies
        """
    )

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == project_path.name


def test_matrix(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {'matrix': [{'version': ['9000', '42']}]})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test.9000
        Checking dependencies
        Creating environment: test.42
        Checking dependencies
        """
    )

    project = Project(project_path)
    assert project.config.envs == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test.9000': {'type': 'virtual', 'skip-install': True},
        'test.42': {'type': 'virtual', 'skip-install': True},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'matrix': [{'version': ['9000', '42']}]},
    }

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = sorted(storage_path.iterdir(), key=lambda d: d.name)
    assert len(env_dirs) == 2

    assert env_dirs[0].name == 'test.42'
    assert env_dirs[1].name == 'test.9000'


def test_incompatible_single(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project, 'default', {'skip-install': True, 'platforms': ['foo'], **project.config.envs['default']}
    )
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Environment `test` is incompatible: unsupported platform
        """
    )

    project = Project(project_path)
    assert project.config.envs == {
        'default': {'type': 'virtual', 'skip-install': True, 'platforms': ['foo']},
        'test': {'type': 'virtual', 'skip-install': True, 'platforms': ['foo']},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True, 'platforms': ['foo']},
        'test': {},
    }

    env_data_path = data_path / 'env' / 'virtual'
    assert not env_data_path.is_dir()


def test_incompatible_matrix_full(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project, 'default', {'skip-install': True, 'platforms': ['foo'], **project.config.envs['default']}
    )
    helpers.update_project_environment(project, 'test', {'matrix': [{'version': ['9000', '42']}]})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Skipped 2 incompatible environments:
        test.9000 -> unsupported platform
        test.42 -> unsupported platform
        """
    )

    project = Project(project_path)
    assert project.config.envs == {
        'default': {'type': 'virtual', 'skip-install': True, 'platforms': ['foo']},
        'test.9000': {'type': 'virtual', 'skip-install': True, 'platforms': ['foo']},
        'test.42': {'type': 'virtual', 'skip-install': True, 'platforms': ['foo']},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True, 'platforms': ['foo']},
        'test': {'matrix': [{'version': ['9000', '42']}]},
    }

    env_data_path = data_path / 'env' / 'virtual'
    assert not env_data_path.is_dir()


def test_incompatible_matrix_partial(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

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

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
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

    project = Project(project_path)
    assert project.config.envs == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test.9000': {'type': 'virtual', 'skip-install': True, 'platforms': ['foo']},
        'test.42': {'type': 'virtual', 'skip-install': True},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {
            'matrix': [{'version': ['9000', '42']}],
            'overrides': {'matrix': {'version': {'platforms': [{'value': 'foo', 'if': ['9000']}]}}},
        },
    }

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    assert env_dirs[0].name == 'test.42'


@pytest.mark.requires_internet
def test_install_project_default_dev_mode(
    hatch, helpers, temp_dir, platform, config_file, extract_installed_requirements
):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Installing project in development mode
        Checking dependencies
        """
    )

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'

    with VirtualEnv(env_path, platform):
        output = platform.run_command(['pip', 'freeze'], check=True, capture_output=True).stdout.decode('utf-8')
        requirements = extract_installed_requirements(output.splitlines())

        assert len(requirements) == 1
        assert requirements[0].lower() == f'-e {str(project_path).lower()}'


@pytest.mark.requires_internet
def test_install_project_no_dev_mode(hatch, helpers, temp_dir, platform, config_file, extract_installed_requirements):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'dev-mode': False, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Installing project
        Checking dependencies
        """
    )

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'

    with VirtualEnv(env_path, platform):
        output = platform.run_command(['pip', 'freeze'], check=True, capture_output=True).stdout.decode('utf-8')
        requirements = extract_installed_requirements(output.splitlines())

        assert len(requirements) == 1
        assert requirements[0].startswith('my-app @')


@pytest.mark.requires_internet
def test_pre_install_commands(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        'default',
        {
            'pre-install-commands': ["python -c \"with open('test.txt', 'w') as f: f.write('content')\""],
            **project.config.envs['default'],
        },
    )
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Running pre-installation commands
        Installing project in development mode
        Checking dependencies
        """
    )
    assert (project_path / 'test.txt').is_file()


def test_pre_install_commands_error(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        'default',
        {'pre-install-commands': ['python -c "import sys;sys.exit(7)"'], **project.config.envs['default']},
    )
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 7
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Running pre-installation commands
        Failed with exit code: 7
        """
    )


@pytest.mark.requires_internet
def test_post_install_commands(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        'default',
        {
            'post-install-commands': ["python -c \"with open('test.txt', 'w') as f: f.write('content')\""],
            **project.config.envs['default'],
        },
    )
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Installing project in development mode
        Running post-installation commands
        Checking dependencies
        """
    )
    assert (project_path / 'test.txt').is_file()


@pytest.mark.requires_internet
def test_post_install_commands_error(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        'default',
        {'post-install-commands': ['python -c "import sys;sys.exit(7)"'], **project.config.envs['default']},
    )
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 7
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Installing project in development mode
        Running post-installation commands
        Failed with exit code: 7
        """
    )


@pytest.mark.requires_internet
def test_sync_dependencies(hatch, helpers, temp_dir, platform, config_file, extract_installed_requirements):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    helpers.update_project_environment(
        project,
        'default',
        {
            'dependencies': ['binary'],
            'post-install-commands': ["python -c \"with open('test.txt', 'w') as f: f.write('content')\""],
            **project.config.envs['default'],
        },
    )
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Installing project in development mode
        Running post-installation commands
        Checking dependencies
        Syncing dependencies
        """
    )
    assert (project_path / 'test.txt').is_file()

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'

    with VirtualEnv(env_path, platform):
        output = platform.run_command(['pip', 'freeze'], check=True, capture_output=True).stdout.decode('utf-8')
        requirements = extract_installed_requirements(output.splitlines())

        assert len(requirements) == 2
        assert requirements[0].startswith('binary==')
        assert requirements[1].lower() == f'-e {str(project_path).lower()}'


@pytest.mark.requires_internet
def test_features(hatch, helpers, temp_dir, platform, config_file, extract_installed_requirements):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project']['optional-dependencies'] = {'foo': ['binary']}
    project.save_config(config)
    helpers.update_project_environment(project, 'default', {'features': ['foo'], **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        Installing project in development mode
        Checking dependencies
        """
    )

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'

    with VirtualEnv(env_path, platform):
        output = platform.run_command(['pip', 'freeze'], check=True, capture_output=True).stdout.decode('utf-8')
        requirements = extract_installed_requirements(output.splitlines())

        assert len(requirements) == 2
        assert requirements[0].startswith('binary==')
        assert requirements[1].lower() == f'-e {str(project_path).lower()}'


def test_no_project_file(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    (project_path / 'pyproject.toml').remove()

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        Checking dependencies
        """
    )

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == project_path.name
