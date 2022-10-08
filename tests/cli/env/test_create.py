import pytest

from hatch.config.constants import AppEnvVars, ConfigEnvVars
from hatch.project.core import Project
from hatch.utils.structures import EnvVars
from hatch.venv.core import VirtualEnv
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT
from hatchling.utils.fs import path_to_uri


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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'


def test_option_absolute_directory(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'test', {'path': str(env_path)})

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
        'test': {'type': 'virtual', 'skip-install': True, 'path': str(env_path)},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'path': str(env_path)},
    }

    assert not env_data_path.is_dir()
    assert env_path.is_dir()


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
    env_path_overridden = temp_dir / 'bar'

    project = Project(project_path)
    assert project.config.envs == {'default': {'type': 'virtual'}}
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {'path': str(env_path_overridden)})

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
        'test': {'type': 'virtual', 'skip-install': True, 'path': str(env_path_overridden)},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'path': str(env_path_overridden)},
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
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {'matrix': [{'version': ['9000', '42']}]})

    with project_path.as_cwd({'VENVS_DIR': '.hatch'}):
        result = hatch('env', 'create')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        Checking dependencies
        """
    )

    with project_path.as_cwd({'VENVS_DIR': '.hatch'}):
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

    env_data_path = project_path / '.hatch'
    assert env_data_path.is_dir()

    env_dirs = list(env_data_path.iterdir())
    assert len(env_dirs) == 4

    assert sorted(entry.name for entry in env_dirs) == ['.gitignore', 'my-app', 'test.42', 'test.9000']


def test_option_local_directory(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'test', {'path': '.venv'})

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
        'test': {'type': 'virtual', 'skip-install': True, 'path': '.venv'},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'path': '.venv'},
    }
    assert not env_data_path.is_dir()
    assert (project_path / '.venv').is_dir()


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
    helpers.update_project_environment(project, 'test', {'path': '.foo'})

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
        'test': {'type': 'virtual', 'skip-install': True, 'path': '.foo'},
    }
    assert project.raw_config['tool']['hatch']['envs'] == {
        'default': {'type': 'virtual', 'skip-install': True},
        'test': {'path': '.foo'},
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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

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
def test_sync_dynamic_dependencies(hatch, helpers, temp_dir, platform, config_file, extract_installed_requirements):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    for i in range(2):
        with temp_dir.as_cwd():
            result = hatch('new', f'{project_name}{i}')

        assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project'].pop('dependencies')
    config['project']['dynamic'].extend(('dependencies', 'optional-dependencies'))
    config['tool']['hatch']['metadata'] = {'allow-direct-references': True, 'hooks': {'custom': {}}}
    project.save_config(config)
    helpers.update_project_environment(
        project,
        'default',
        {
            'dependencies': ['my-app1 @ {root:uri}/../my-app1'],
            'features': ['foo'],
            'post-install-commands': ["python -c \"with open('test.txt', 'w') as f: f.write('content')\""],
            **project.config.envs['default'],
        },
    )
    helpers.update_project_environment(project, 'test', {})

    build_script = project_path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            from hatchling.metadata.plugin.interface import MetadataHookInterface

            class CustomHook(MetadataHookInterface):
                def update(self, metadata):
                    metadata['dependencies'] = ['my-app0 @ {root:uri}/../my-app0']
                    metadata['optional-dependencies'] = {'foo': ['binary']}
            """
        )
    )

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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == 'test'

    with VirtualEnv(env_path, platform):
        output = platform.run_command(['pip', 'freeze'], check=True, capture_output=True).stdout.decode('utf-8')
        requirements = extract_installed_requirements(output.splitlines())

        assert len(requirements) == 4
        assert requirements[0].startswith('binary==')
        assert requirements[1].lower() == f'-e {str(project_path).lower()}'
        assert requirements[2].lower() == f'my-app0 @ {path_to_uri(project_path).lower()}/../my-app0'
        assert requirements[3].lower() == f'my-app1 @ {path_to_uri(project_path).lower()}/../my-app1'


@pytest.mark.requires_internet
def test_unknown_dynamic_feature(hatch, helpers, temp_dir, platform, config_file, extract_installed_requirements):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    with temp_dir.as_cwd():
        result = hatch('new', f'{project_name}1')

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    project = Project(project_path)
    config = dict(project.raw_config)
    config['build-system']['requires'].append(f'my-app1 @ {path_to_uri(project_path).lower()}/../my-app1')
    config['project']['dynamic'].append('optional-dependencies')
    config['tool']['hatch']['metadata'] = {'hooks': {'custom': {}}}
    project.save_config(config)
    helpers.update_project_environment(
        project,
        'default',
        {
            'features': ['foo'],
            'post-install-commands': ["python -c \"with open('test.txt', 'w') as f: f.write('content')\""],
            **project.config.envs['default'],
        },
    )
    helpers.update_project_environment(project, 'test', {})

    build_script = project_path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            from hatchling.metadata.plugin.interface import MetadataHookInterface

            class CustomHook(MetadataHookInterface):
                def update(self, metadata):
                    metadata['optional-dependencies'] = {'bar': ['binary']}
            """
        )
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        with pytest.raises(
            ValueError,
            match=(
                'Feature `foo` of field `tool.hatch.envs.test.features` is not defined in the dynamic '
                'field `project.optional-dependencies`'
            ),
        ):
            hatch('env', 'create', 'test')


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

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 1

    env_path = env_dirs[0]

    assert env_path.name == project_path.name
