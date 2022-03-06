import pytest

from hatch.project.core import Project
from hatch.utils.structures import EnvVars


@pytest.fixture(scope='module', autouse=True)
def terminal_width():
    with EnvVars({'COLUMNS': '200'}):
        yield


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
        result = hatch('env', 'show', '--ascii')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
             Standalone
        +---------+---------+
        | Name    | Type    |
        +=========+=========+
        | default | virtual |
        +---------+---------+
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
        result = hatch('env', 'show', '--ascii')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
             Standalone
        +---------+---------+
        | Name    | Type    |
        +=========+=========+
        | default | virtual |
        +---------+---------+
        | foo     | virtual |
        +---------+---------+
        | bar     | virtual |
        +---------+---------+
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
        result = hatch('env', 'show', '--ascii')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
             Standalone
        +---------+---------+
        | Name    | Type    |
        +=========+=========+
        | default | virtual |
        +---------+---------+
                     Matrices
        +------+---------+----------------+
        | Name | Type    | Envs           |
        +======+=========+================+
        | foo  | virtual | foo.py39-9000  |
        |      |         | foo.py39-3.14  |
        |      |         | foo.py310-9000 |
        |      |         | foo.py310-3.14 |
        +------+---------+----------------+
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
        result = hatch('env', 'show', '--ascii')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
                     Matrices
        +---------+---------+------------+
        | Name    | Type    | Envs       |
        +=========+=========+============+
        | default | virtual | py39-9000  |
        |         |         | py39-3.14  |
        |         |         | py310-9000 |
        |         |         | py310-3.14 |
        +---------+---------+------------+
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
        result = hatch('env', 'show', '--ascii')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
            Standalone
        +------+---------+
        | Name | Type    |
        +======+=========+
        | bar  | virtual |
        +------+---------+
                       Matrices
        +---------+---------+----------------+
        | Name    | Type    | Envs           |
        +=========+=========+================+
        | default | virtual | py39-9000      |
        |         |         | py39-3.14      |
        |         |         | py310-9000     |
        |         |         | py310-3.14     |
        +---------+---------+----------------+
        | foo     | virtual | foo.py39-9000  |
        |         |         | foo.py39-3.14  |
        |         |         | foo.py310-9000 |
        |         |         | foo.py310-3.14 |
        +---------+---------+----------------+
        """
    )


def test_optional_columns(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    dependencies = ['python___dateutil', 'bAr.Baz[TLS]   >=1.2RC5', 'Foo;python_version<"3.8"']
    env_vars = {'FOO': '1', 'BAR': '2'}
    description = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna \
aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. \
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint \
occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
"""
    project = Project(project_path)
    helpers.update_project_environment(
        project,
        'default',
        {
            'matrix': [{'version': ['9000', '3.14'], 'py': ['39', '310']}],
            'description': description,
            'dependencies': dependencies,
            'env-vars': env_vars,
        },
    )
    helpers.update_project_environment(
        project, 'foo', {'description': description, 'dependencies': dependencies, 'env-vars': env_vars}
    )

    with project_path.as_cwd():
        result = hatch('env', 'show', '--ascii')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
                                                                                                       Standalone
        +------+---------+-----------------------------+-----------------------+-------------------------------------------------------------------------------------------------------------------------------+
        | Name | Type    | Dependencies                | Environment variables | Description                                                                                                                   |
        +======+=========+=============================+=======================+===============================================================================================================================+
        | foo  | virtual | bar-baz[tls]>=1.2rc5        | BAR=2                 | Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.   |
        |      |         | foo; python_version < '3.8' | FOO=1                 | Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure   |
        |      |         | python-dateutil             |                       | dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non  |
        |      |         |                             |                       | proident, sunt in culpa qui officia deserunt mollit anim id est laborum.                                                      |
        +------+---------+-----------------------------+-----------------------+-------------------------------------------------------------------------------------------------------------------------------+
                                                                                                        Matrices
        +---------+---------+------------+-----------------------------+-----------------------+---------------------------------------------------------------------------------------------------------------+
        | Name    | Type    | Envs       | Dependencies                | Environment variables | Description                                                                                                   |
        +=========+=========+============+=============================+=======================+===============================================================================================================+
        | default | virtual | py39-9000  | bar-baz[tls]>=1.2rc5        | BAR=2                 | Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore |
        |         |         | py39-3.14  | foo; python_version < '3.8' | FOO=1                 | magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea        |
        |         |         | py310-9000 | python-dateutil             |                       | commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat     |
        |         |         | py310-3.14 |                             |                       | nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit     |
        |         |         |            |                             |                       | anim id est laborum.                                                                                          |
        +---------+---------+------------+-----------------------------+-----------------------+---------------------------------------------------------------------------------------------------------------+
        """  # noqa: E501
    )
