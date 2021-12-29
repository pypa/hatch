import sys

from hatch.config.constants import AppEnvVars, ConfigEnvVars
from hatch.project.core import Project
from hatch.utils.structures import EnvVars


def test_automatic_creation(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('run', 'python', '-c', "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

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

    assert str(env_path) in str(output_file.read_text())


def test_enter_project_directory(hatch, config_file, helpers, temp_dir):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My App'

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

    with EnvVars({ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('run', 'python', '-c', "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

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

    assert str(env_path) in str(output_file.read_text())


def test_sync_dependencies(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'default')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
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

    project = Project(project_path)
    helpers.update_project_environment(
        project, 'default', {'dependencies': ['binary'], **project.config.envs['default']}
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch(
            'run',
            'python',
            '-c',
            "import binary,pathlib,sys;pathlib.Path('test.txt').write_text(str(binary.convert_units(1024)))",
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Syncing dependencies
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

    assert str(output_file.read_text()) == "(1.0, 'KiB')"


def test_scripts(hatch, helpers, temp_dir, config_file):
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
        project, 'default', {'skip-install': True, 'scripts': {'py': 'python -c'}, **project.config.envs['default']}
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('run', 'py', "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

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

    assert str(env_path) in str(output_file.read_text())


def test_scripts_specific_environment(hatch, helpers, temp_dir, config_file):
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
        project, 'default', {'skip-install': True, 'scripts': {'py': 'python -c'}, **project.config.envs['default']}
    )
    helpers.update_project_environment(project, 'test', {'env-vars': {'foo': 'bar'}})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch(
            'run',
            'test:py',
            "import os,pathlib,sys;pathlib.Path('test.txt').write_text("
            "sys.executable+os.linesep[-1]+os.environ['foo'])",
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: test
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

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

    python_executable_path, env_var_value = str(output_file.read_text()).splitlines()
    assert str(env_path) in python_executable_path
    assert env_var_value == 'bar'


def test_scripts_no_environment(hatch, temp_dir, config_file):
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
    config = dict(project.raw_config)
    config['tool']['hatch']['scripts'] = {'py': 'python -c'}
    project.save_config(config)

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('run', ':py', "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)")

    assert result.exit_code == 0, result.output
    assert not result.output
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

    env_data_path = data_path / 'env' / 'virtual'
    assert not env_data_path.exists()

    assert output_file.read_text().strip().lower() == sys.executable.lower()


def test_error(hatch, helpers, temp_dir, config_file):
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
        result = hatch('run', 'error')

    assert result.exit_code == 3
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        """
    )
    output_file = project_path / 'test.txt'
    assert not output_file.is_file()


def test_matrix(hatch, helpers, temp_dir, config_file, legacy_windows_terminal):
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
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {'matrix': [{'version': ['9000', '42']}]})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch(
            'run', 'test:python', '-c', "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])"
        )

    padding = '' if legacy_windows_terminal else '─'
    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {padding}───────────────────────────────── test.9000 ──────────────────────────────────{padding}
        Creating environment: test.9000
        {padding}────────────────────────────────── test.42 ───────────────────────────────────{padding}
        Creating environment: test.42
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

    env_data_path = data_path / 'env' / 'virtual'
    assert env_data_path.is_dir()

    storage_dirs = list(env_data_path.iterdir())
    assert len(storage_dirs) == 1

    storage_path = storage_dirs[0]

    project_part = f'{project_path.name}-'
    assert storage_path.name.startswith(project_part)

    hash_part = storage_path.name[len(project_part) :]
    assert len(hash_part) == 8

    env_dirs = sorted(storage_path.iterdir(), key=lambda d: d.name)[::-1]
    assert len(env_dirs) == 2

    python_path1, python_path2 = str(output_file.read_text()).splitlines()
    for python_path, env_dir, env_name in zip((python_path1, python_path2), env_dirs, ('test.9000', 'test.42')):
        assert env_dir.name == env_name
        assert str(env_dir) in python_path


def test_incompatible_single(hatch, helpers, temp_dir, config_file):
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
        project, 'default', {'skip-install': True, 'platforms': ['foo'], **project.config.envs['default']}
    )
    helpers.update_project_environment(project, 'test', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch(
            'run', 'test:python', '-c', "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])"
        )

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Environment `test` is incompatible: unsupported platform
        """
    )
    output_file = project_path / 'test.txt'
    assert not output_file.is_file()

    env_data_path = data_path / 'env' / 'virtual'
    assert not env_data_path.is_dir()


def test_incompatible_matrix_full(hatch, helpers, temp_dir, config_file):
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
        project, 'default', {'skip-install': True, 'platforms': ['foo'], **project.config.envs['default']}
    )
    helpers.update_project_environment(project, 'test', {'matrix': [{'version': ['9000', '42']}]})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch(
            'run', 'test:python', '-c', "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])"
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Skipped 2 incompatible environments:
        test.9000 -> unsupported platform
        test.42 -> unsupported platform
        """
    )
    output_file = project_path / 'test.txt'
    assert not output_file.is_file()

    env_data_path = data_path / 'env' / 'virtual'
    assert not env_data_path.is_dir()


def test_incompatible_matrix_partial(hatch, helpers, temp_dir, config_file, legacy_windows_terminal):
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
        result = hatch(
            'run', 'test:python', '-c', "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])"
        )

    padding = '' if legacy_windows_terminal else '─'
    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {padding}────────────────────────────────── test.42 ───────────────────────────────────{padding}
        Creating environment: test.42

        Skipped 1 incompatible environment:
        test.9000 -> unsupported platform
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

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
    assert env_path.name == 'test.42'

    python_path = str(output_file.read_text()).strip()
    assert str(env_path) in python_path


def test_incompatible_missing_python(hatch, helpers, temp_dir, config_file, legacy_windows_terminal):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'
    data_path = temp_dir / 'data'
    data_path.mkdir()

    known_version = ''.join(map(str, sys.version_info[:2]))
    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'test', {'matrix': [{'python': [known_version, '9000']}]})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch(
            'run', 'test:python', '-c', "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])"
        )

    padding = '' if legacy_windows_terminal else '─'
    left_pad = padding
    right_pad = padding + ('─' if len(known_version) < 3 else '')
    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {left_pad}───────────────────────────────── test.py{known_version} ─────────────────────────────────{right_pad}
        Creating environment: test.py{known_version}

        Skipped 1 incompatible environment:
        test.py9000 -> cannot locate Python: 9000
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

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
    assert env_path.name == f'test.py{known_version}'

    python_path = str(output_file.read_text()).strip()
    assert str(env_path) in python_path


def test_env_detection(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'foo', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        """
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'foo')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: foo
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

    env_dirs = sorted(storage_path.iterdir(), key=lambda d: d.name)
    assert len(env_dirs) == 2

    assert env_dirs[0].name == 'foo'
    assert env_dirs[1].name == 'my-app'

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path), AppEnvVars.ENV_ACTIVE: 'foo'}):
        result = hatch('run', 'python', '-c', "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)")

    assert result.exit_code == 0, result.output

    output_file = project_path / 'test.txt'
    assert output_file.is_file()

    python_path = str(output_file.read_text()).strip()
    assert str(env_dirs[0]) in python_path


def test_env_detection_override(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'default', {'skip-install': True, **project.config.envs['default']})
    helpers.update_project_environment(project, 'foo', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        """
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'foo')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: foo
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

    env_dirs = sorted(storage_path.iterdir(), key=lambda d: d.name)
    assert len(env_dirs) == 2

    assert env_dirs[0].name == 'foo'
    assert env_dirs[1].name == 'my-app'

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path), AppEnvVars.ENV_ACTIVE: 'foo'}):
        result = hatch(
            'run', 'default:python', '-c', "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)"
        )

    assert result.exit_code == 0, result.output

    output_file = project_path / 'test.txt'
    assert output_file.is_file()

    python_path = str(output_file.read_text()).strip()
    assert str(env_dirs[1]) in python_path
