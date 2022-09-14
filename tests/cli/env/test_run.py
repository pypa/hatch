from hatch.config.constants import ConfigEnvVars
from hatch.project.core import Project


def test_filter_not_mapping(hatch, helpers, temp_dir, config_file):
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
            'skip-install': True,
            'scripts': {
                'error': [
                    'python -c "import sys;sys.exit(3)"',
                    'python -c "import pathlib,sys;pathlib.Path(\'test.txt\').write_text(sys.executable)"',
                ],
            },
            **project.config.envs['default'],
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'run', 'error', '--filter', '[]')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        The --filter/-f option must be a JSON mapping
        """
    )


def test_filter(hatch, helpers, temp_dir, config_file):
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
            'overrides': {'matrix': {'version': {'foo-bar-option': {'value': True, 'if': ['42']}}}},
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch(
            'env',
            'run',
            '--env',
            'test',
            '--filter',
            '{"foo-bar-option":true}',
            '--',
            'python',
            '-c',
            "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])",
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        ─────────────────────────────────── test.42 ────────────────────────────────────
        Creating environment: test.42
        Checking dependencies
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

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
    assert env_path.name == 'test.42'

    python_path = str(output_file.read_text()).strip()
    assert str(env_path) in python_path


def test_force_continue(hatch, helpers, temp_dir, config_file):
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
            'skip-install': True,
            'scripts': {
                'error': [
                    'python -c "import sys;sys.exit(2)"',
                    '- python -c "import sys;sys.exit(3)"',
                    'python -c "import sys;sys.exit(1)"',
                    'python -c "import pathlib,sys;pathlib.Path(\'test.txt\').write_text(sys.executable)"',
                ],
            },
            **project.config.envs['default'],
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'run', '--force-continue', '--', 'error')

    assert result.exit_code == 2
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        Checking dependencies
        cmd [1] | python -c "import sys;sys.exit(2)"
        cmd [2] | - python -c "import sys;sys.exit(3)"
        cmd [3] | python -c "import sys;sys.exit(1)"
        cmd [4] | python -c "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)"
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

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

    assert str(env_path) in str(output_file.read_text())


def test_ignore_compatibility(hatch, helpers, temp_dir, config_file):
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
        result = hatch(
            'env',
            'run',
            '--ignore-compat',
            '--env',
            'test',
            '--',
            'python',
            '-c',
            "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])",
        )

    assert result.exit_code == 0
    assert result.output == helpers.dedent(
        """
        Skipped 1 incompatible environment:
        test -> unsupported platform
        """
    )
    output_file = project_path / 'test.txt'
    assert not output_file.is_file()

    env_data_path = data_path / 'env' / 'virtual'
    assert not env_data_path.is_dir()
