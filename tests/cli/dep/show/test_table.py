import pytest

from hatch.project.core import Project
from hatch.utils.structures import EnvVars


@pytest.fixture(scope='module', autouse=True)
def terminal_width():
    with EnvVars({'COLUMNS': '200'}):
        yield


def test_incompatible_environment(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    project = Project(path)
    config = dict(project.raw_config)
    config['build-system']['requires'].append('foo')
    config['project']['dynamic'].append('dependencies')
    project.save_config(config)
    helpers.update_project_environment(
        project, 'default', {'skip-install': True, 'python': '9000', **project.config.envs['default']}
    )

    with path.as_cwd():
        result = hatch('dep', 'show', 'table')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Environment `default` is incompatible: cannot locate Python: 9000
        """
    )


def test_project_only(hatch, helpers, temp_dir, config_file):
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
    config['project']['dependencies'] = ['foo-bar-baz']
    project.save_config(config)

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'table', '--ascii', '-p')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
            Project
        +-------------+
        | Name        |
        +=============+
        | foo-bar-baz |
        +-------------+
        """
    )


def test_environment_only(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'default', {'dependencies': ['foo-bar-baz']})

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'table', '--ascii', '-e')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
         Env: default
        +-------------+
        | Name        |
        +=============+
        | foo-bar-baz |
        +-------------+
        """
    )


def test_default_both(hatch, helpers, temp_dir, config_file):
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
    config['project']['dependencies'] = ['foo-bar-baz']
    project.save_config(config)
    helpers.update_project_environment(project, 'default', {'dependencies': ['baz-bar-foo']})

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'table', '--ascii')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
            Project
        +-------------+
        | Name        |
        +=============+
        | foo-bar-baz |
        +-------------+
         Env: default
        +-------------+
        | Name        |
        +=============+
        | baz-bar-foo |
        +-------------+
        """
    )


def test_optional_columns(hatch, helpers, temp_dir, config_file):
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
    config['project']['dependencies'] = [
        'python___dateutil',
        'bAr.Baz[TLS, EdDSA]   >=1.2RC5',
        'Foo;python_version<"3.8"',
    ]
    project.save_config(config)
    helpers.update_project_environment(
        project,
        'default',
        {
            'dependencies': [
                'proj @ git+https://github.com/org/proj.git@v1',
                'bAr.Baz   [TLS, EdDSA]   >=1.2RC5;python_version<"3.8"',
            ],
        },
    )

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'table', '--ascii')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
                                      Project
        +-----------------+----------+------------------------+------------+
        | Name            | Versions | Markers                | Features   |
        +=================+==========+========================+============+
        | bar-baz         | >=1.2rc5 |                        | eddsa, tls |
        | foo             |          | python_version < '3.8' |            |
        | python-dateutil |          |                        |            |
        +-----------------+----------+------------------------+------------+
                                                    Env: default
        +---------+----------------------------------------+----------+------------------------+------------+
        | Name    | URL                                    | Versions | Markers                | Features   |
        +=========+========================================+==========+========================+============+
        | bar-baz |                                        | >=1.2rc5 | python_version < '3.8' | eddsa, tls |
        | proj    | git+https://github.com/org/proj.git@v1 |          |                        |            |
        +---------+----------------------------------------+----------+------------------------+------------+
        """
    )
