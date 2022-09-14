import pytest

from hatch.config.constants import AppEnvVars
from hatch.project.core import Project


def test_unknown_type(hatch, helpers, temp_dir_data, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir_data.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir_data / 'my-app'

    project = Project(project_path)
    config = dict(project.config.envs['default'])
    config['type'] = 'foo'
    helpers.update_project_environment(project, 'default', config)

    with project_path.as_cwd():
        result = hatch('env', 'prune')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Environment `default` has unknown type: foo
        """
    )


@pytest.mark.requires_internet
def test_all(hatch, helpers, temp_dir_data, config_file):
    project_name = 'My.App'

    with temp_dir_data.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir_data / 'my-app'

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

    env_data_path = temp_dir_data / 'data' / 'env' / 'virtual'
    assert env_data_path.is_dir()

    project_data_path = env_data_path / project_path.name
    assert project_data_path.is_dir()

    storage_dirs = list(project_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]
    assert len(storage_path.name) == 8

    env_dirs = list(storage_path.iterdir())
    assert len(env_dirs) == 2

    with project_path.as_cwd():
        result = hatch('env', 'prune')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Removing environment: foo
        Removing environment: bar
        """
    )

    assert not storage_path.is_dir()


def test_incompatible_ok(hatch, helpers, temp_dir_data, config_file):
    project_name = 'My.App'

    with temp_dir_data.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir_data / 'my-app'

    project = Project(project_path)
    helpers.update_project_environment(
        project, 'default', {'skip-install': True, 'platforms': ['foo'], **project.config.envs['default']}
    )

    with project_path.as_cwd():
        result = hatch('env', 'prune')

    assert result.exit_code == 0, result.output
    assert not result.output


def test_active(hatch, temp_dir_data, helpers, config_file):
    project_name = 'My.App'

    with temp_dir_data.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir_data / 'my-app'

    with project_path.as_cwd(env_vars={AppEnvVars.ENV_ACTIVE: 'default'}):
        result = hatch('env', 'prune')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Cannot remove active environment: default
        """
    )
