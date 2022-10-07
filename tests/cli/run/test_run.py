import sys

import pytest

from hatch.config.constants import AppEnvVars, ConfigEnvVars
from hatch.project.core import Project
from hatch.utils.structures import EnvVars


def test_help(hatch):
    short = hatch('run', '-h')
    assert short.exit_code == 0, short.output

    long = hatch('run', '--help')
    assert long.exit_code == 0, long.output

    assert short.output == long.output


def test_automatic_creation(hatch, helpers, temp_dir, config_file):
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
        result = hatch('run', 'python', '-c', "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
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

    assert env_path.name == project_path.name

    assert str(env_path) in str(output_file.read_text())


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

    with EnvVars({ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('run', 'python', '-c', "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
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

    assert env_path.name == project_path.name

    assert str(env_path) in str(output_file.read_text())


@pytest.mark.requires_internet
def test_sync_dependencies(hatch, helpers, temp_dir, config_file):
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
        result = hatch('env', 'create', 'default')

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
        Checking dependencies
        Syncing dependencies
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

    assert str(output_file.read_text()) == "(1.0, 'KiB')"


@pytest.mark.requires_internet
def test_sync_project_dependencies(hatch, helpers, temp_dir, config_file):
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
        result = hatch('env', 'create', 'default')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
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

    assert env_path.name == project_path.name

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project']['dependencies'] = ['binary']
    project.save_config(config)

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
        Checking dependencies
        Syncing dependencies
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

    assert str(output_file.read_text()) == "(1.0, 'KiB')"


@pytest.mark.requires_internet
def test_sync_project_features(hatch, helpers, temp_dir, config_file):
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
    config['project']['optional-dependencies'] = {'foo': []}
    project.save_config(config)
    helpers.update_project_environment(project, 'default', {'features': ['foo'], **project.config.envs['default']})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'default')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
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

    assert env_path.name == project_path.name

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project']['optional-dependencies']['foo'].append('binary')
    project.save_config(config)

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
        Checking dependencies
        Syncing dependencies
        """
    )
    output_file = project_path / 'test.txt'
    assert output_file.is_file()

    assert str(output_file.read_text()) == "(1.0, 'KiB')"


def test_scripts(hatch, helpers, temp_dir, config_file):
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
        {'skip-install': True, 'scripts': {'py': 'python -c {args}'}, **project.config.envs['default']},
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('run', 'py', "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
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

    assert env_path.name == project_path.name

    assert str(env_path) in str(output_file.read_text())


def test_scripts_specific_environment(hatch, helpers, temp_dir, config_file):
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
        {'skip-install': True, 'scripts': {'py': 'python -c {args}'}, **project.config.envs['default']},
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

    assert env_path.name == 'test'

    python_executable_path, env_var_value = str(output_file.read_text()).splitlines()
    assert str(env_path) in python_executable_path
    assert env_var_value == 'bar'


@pytest.mark.requires_internet
def test_scripts_no_environment(hatch, helpers, temp_dir, config_file):
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
    config['tool']['hatch']['scripts'] = {'py': 'python -c {args}'}
    project.save_config(config)

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('run', ':py', "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Checking dependencies
        """
    )

    output_file = project_path / 'test.txt'
    assert output_file.is_file()

    env_data_path = data_path / 'env' / 'virtual'
    assert not env_data_path.exists()

    assert output_file.read_text().strip().lower() == sys.executable.lower()


def test_error(hatch, helpers, temp_dir, config_file):
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
        result = hatch('run', 'error')

    assert result.exit_code == 3
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        Checking dependencies
        cmd [1] | python -c "import sys;sys.exit(3)"
        """
    )
    output_file = project_path / 'test.txt'
    assert not output_file.is_file()


def test_ignore_error(hatch, helpers, temp_dir, config_file):
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
                    '- python -c "import sys;sys.exit(3)"',
                    'python -c "import pathlib,sys;pathlib.Path(\'test.txt\').write_text(sys.executable)"',
                ],
            },
            **project.config.envs['default'],
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('run', 'error')

    assert result.exit_code == 0
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        Checking dependencies
        cmd [1] | - python -c "import sys;sys.exit(3)"
        cmd [2] | python -c "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)"
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


def test_command_expansion_error(hatch, helpers, temp_dir, config_file):
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
        {'skip-install': True, 'scripts': {'error': ['echo {env:FOOBAR}']}, **project.config.envs['default']},
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('run', 'error')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        Checking dependencies
        Nonexistent environment variable must set a default: FOOBAR
        """
    )
    output_file = project_path / 'test.txt'
    assert not output_file.is_file()


def test_verbosity(hatch, helpers, temp_dir, config_file):
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
                'write-exe': [
                    'python -c "import pathlib,sys;pathlib.Path(\'{args}1.txt\').write_text(sys.executable)"',
                    'python -c "import pathlib,sys;pathlib.Path(\'{args}2.txt\').write_text(sys.executable)"',
                    'python -c "import pathlib,sys;pathlib.Path(\'{args}3.txt\').write_text(sys.executable)"',
                ],
            },
            **project.config.envs['default'],
        },
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('-v', 'run', 'write-exe', 'test')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        ─────────────────────────────────── default ────────────────────────────────────
        Creating environment: default
        Checking dependencies
        cmd [1] | python -c "import pathlib,sys;pathlib.Path('test1.txt').write_text(sys.executable)"
        cmd [2] | python -c "import pathlib,sys;pathlib.Path('test2.txt').write_text(sys.executable)"
        cmd [3] | python -c "import pathlib,sys;pathlib.Path('test3.txt').write_text(sys.executable)"
        """
    )
    output_files = []
    for i in range(1, 4):
        output_file = project_path / f'test{i}.txt'
        assert output_file.is_file()
        output_files.append(output_file)

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

    for output_file in output_files:
        assert str(env_path) in str(output_file.read_text())


def test_matrix_no_environments(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'test', {'matrix': []})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch(
            'run', 'test:python', '-c', "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])"
        )

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        No variables defined for matrix: test
        """
    )


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
        result = hatch(
            'run', 'test:python', '-c', "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])"
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        ────────────────────────────────── test.9000 ───────────────────────────────────
        Creating environment: test.9000
        Checking dependencies
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

    env_dirs = sorted(storage_path.iterdir(), key=lambda d: d.name)[::-1]
    assert len(env_dirs) == 2

    python_path1, python_path2 = str(output_file.read_text()).splitlines()
    for python_path, env_dir, env_name in zip((python_path1, python_path2), env_dirs, ('test.9000', 'test.42')):
        assert env_dir.name == env_name
        assert str(env_dir) in python_path


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
        result = hatch(
            'run', 'test:python', '-c', "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])"
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        ─────────────────────────────────── test.42 ────────────────────────────────────
        Creating environment: test.42
        Checking dependencies

        Skipped 1 incompatible environment:
        test.9000 -> unsupported platform
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


def test_incompatible_missing_python(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

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

    padding = '─'
    if len(known_version) < 3:
        padding += '─'

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        ────────────────────────────────── test.py{known_version} ─────────────────────────────────{padding}
        Creating environment: test.py{known_version}
        Checking dependencies

        Skipped 1 incompatible environment:
        test.py9000 -> cannot locate Python: 9000
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
    assert env_path.name == f'test.py{known_version}'

    python_path = str(output_file.read_text()).strip()
    assert str(env_path) in python_path


def test_env_detection(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'foo', {})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
        Checking dependencies
        """
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'foo')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: foo
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

    project_name = 'My.App'

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
        Checking dependencies
        """
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch('env', 'create', 'foo')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: foo
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


def test_matrix_variable_selection_no_command(hatch, helpers, temp_dir, config_file):
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
        result = hatch('run', '+version=9000')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Missing argument `MATRIX:ARGS...`
        """
    )


def test_matrix_variable_selection_duplicate_inclusion(hatch, helpers, temp_dir, config_file):
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
        result = hatch(
            'run',
            '+version=9000',
            '+version=42',
            'python',
            '-c',
            "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)",
        )

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Duplicate included variable: version
        """
    )


def test_matrix_variable_selection_duplicate_exclusion(hatch, helpers, temp_dir, config_file):
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
        result = hatch(
            'run',
            '-version=9000',
            '-version=42',
            'python',
            '-c',
            "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)",
        )

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Duplicate excluded variable: version
        """
    )


def test_matrix_variable_selection_python_alias(hatch, helpers, temp_dir, config_file):
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
    helpers.update_project_environment(project, 'test', {'matrix': [{'python': ['9000', '42']}]})

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch(
            'run',
            '+py=9000',
            '+python=42',
            'python',
            '-c',
            "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)",
        )

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Duplicate included variable: python
        """
    )


def test_matrix_variable_selection_not_matrix(hatch, helpers, temp_dir, config_file):
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
        result = hatch(
            'run',
            '+version=9000',
            'python',
            '-c',
            "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])",
        )

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Variable selection is unsupported for non-matrix environments: default
        """
    )


def test_matrix_variable_selection_inclusion(hatch, helpers, temp_dir, config_file):
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
        result = hatch(
            'run',
            '+version=9000',
            'test:python',
            '-c',
            "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])",
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        ────────────────────────────────── test.9000 ───────────────────────────────────
        Creating environment: test.9000
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
    assert env_path.name == 'test.9000'

    python_path = str(output_file.read_text()).strip()
    assert str(env_path) in python_path


def test_matrix_variable_selection_exclusion(hatch, helpers, temp_dir, config_file):
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
        result = hatch(
            'run',
            '-version=9000',
            'test:python',
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


def test_matrix_variable_selection_exclude_all(hatch, helpers, temp_dir, config_file):
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
        result = hatch(
            'run',
            '-version',
            'test:python',
            '-c',
            "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])",
        )

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        No environments were selected
        """
    )


def test_matrix_variable_selection_include_none(hatch, helpers, temp_dir, config_file):
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
        result = hatch(
            'run',
            '+version=3.14',
            'test:python',
            '-c',
            "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])",
        )

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        No environments were selected
        """
    )


def test_matrix_variable_selection_inclusion_multiple_variables(hatch, helpers, temp_dir, config_file):
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
        project, 'test', {'matrix': [{'version1': ['9000', '42'], 'version2': ['3.14']}]}
    )

    with project_path.as_cwd(env_vars={ConfigEnvVars.DATA: str(data_path)}):
        result = hatch(
            'run',
            '+version1=9000',
            'test:python',
            '-c',
            "import os,sys;open('test.txt', 'a').write(sys.executable+os.linesep[-1])",
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        ──────────────────────────────── test.9000-3.14 ────────────────────────────────
        Creating environment: test.9000-3.14
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
    assert env_path.name == 'test.9000-3.14'

    python_path = str(output_file.read_text()).strip()
    assert str(env_path) in python_path


def test_context_formatting_recursion(hatch, helpers, temp_dir, config_file):
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
            'scripts': {'py': 'python -c "{env:FOO:{env:BAR:{env:BAZ}}}"'},
            **project.config.envs['default'],
        },
    )

    with project_path.as_cwd(
        env_vars={
            ConfigEnvVars.DATA: str(data_path),
            'BAZ': "import pathlib,sys;pathlib.Path('test.txt').write_text(sys.executable)",
        }
    ):
        result = hatch('run', 'py')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Creating environment: default
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

    assert env_path.name == project_path.name

    assert str(env_path) in str(output_file.read_text())
