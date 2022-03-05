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
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
             Standalone
        ┌─────────┬─────────┐
        │ Name    │ Type    │
        ├─────────┼─────────┤
        │ default │ virtual │
        └─────────┴─────────┘
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
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
             Standalone
        ┌─────────┬─────────┐
        │ Name    │ Type    │
        ├─────────┼─────────┤
        │ default │ virtual │
        ├─────────┼─────────┤
        │ foo     │ virtual │
        ├─────────┼─────────┤
        │ bar     │ virtual │
        └─────────┴─────────┘
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
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
             Standalone
        ┌─────────┬─────────┐
        │ Name    │ Type    │
        ├─────────┼─────────┤
        │ default │ virtual │
        └─────────┴─────────┘
                     Matrices
        ┌──────┬─────────┬────────────────┐
        │ Name │ Type    │ Envs           │
        ├──────┼─────────┼────────────────┤
        │ foo  │ virtual │ foo.py39-9000  │
        │      │         │ foo.py39-3.14  │
        │      │         │ foo.py310-9000 │
        │      │         │ foo.py310-3.14 │
        └──────┴─────────┴────────────────┘
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
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
                     Matrices
        ┌─────────┬─────────┬────────────┐
        │ Name    │ Type    │ Envs       │
        ├─────────┼─────────┼────────────┤
        │ default │ virtual │ py39-9000  │
        │         │         │ py39-3.14  │
        │         │         │ py310-9000 │
        │         │         │ py310-3.14 │
        └─────────┴─────────┴────────────┘
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
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
            Standalone
        ┌──────┬─────────┐
        │ Name │ Type    │
        ├──────┼─────────┤
        │ bar  │ virtual │
        └──────┴─────────┘
                       Matrices
        ┌─────────┬─────────┬────────────────┐
        │ Name    │ Type    │ Envs           │
        ├─────────┼─────────┼────────────────┤
        │ default │ virtual │ py39-9000      │
        │         │         │ py39-3.14      │
        │         │         │ py310-9000     │
        │         │         │ py310-3.14     │
        ├─────────┼─────────┼────────────────┤
        │ foo     │ virtual │ foo.py39-9000  │
        │         │         │ foo.py39-3.14  │
        │         │         │ foo.py310-9000 │
        │         │         │ foo.py310-3.14 │
        └─────────┴─────────┴────────────────┘
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
    project = Project(project_path)
    helpers.update_project_environment(
        project,
        'default',
        {
            'matrix': [{'version': ['9000', '3.14'], 'py': ['39', '310']}],
            'dependencies': dependencies,
            'env-vars': env_vars,
        },
    )
    helpers.update_project_environment(project, 'foo', {'dependencies': dependencies, 'env-vars': env_vars})

    with project_path.as_cwd():
        result = hatch('env', 'show')

    assert result.exit_code == 0, result.output
    assert helpers.remove_trailing_spaces(result.output) == helpers.dedent(
        """
                                       Standalone
        ┌──────┬─────────┬─────────────────────────────┬───────────────────────┐
        │ Name │ Type    │ Dependencies                │ Environment variables │
        ├──────┼─────────┼─────────────────────────────┼───────────────────────┤
        │ foo  │ virtual │ bar-baz[tls]>=1.2rc5        │ BAR=2                 │
        │      │         │ foo; python_version < '3.8' │ FOO=1                 │
        │      │         │ python-dateutil             │                       │
        └──────┴─────────┴─────────────────────────────┴───────────────────────┘
                                           Matrices
        ┌───────┬───────┬──────────┬───────────────────────────┬─────────────────────┐
        │ Name  │ Type  │ Envs     │ Dependencies              │ Environment variab… │
        ├───────┼───────┼──────────┼───────────────────────────┼─────────────────────┤
        │ defa… │ virt… │ py39-90… │ bar-baz[tls]>=1.2rc5      │ BAR=2               │
        │       │       │ py39-3.… │ foo; python_version < '3… │ FOO=1               │
        │       │       │ py310-9… │ python-dateutil           │                     │
        │       │       │ py310-3… │                           │                     │
        └───────┴───────┴──────────┴───────────────────────────┴─────────────────────┘
        """
    )
