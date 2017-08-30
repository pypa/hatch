import glob
import json
import io
import os
import re
import subprocess
import sys
import time
from tempfile import TemporaryDirectory

import click
from atomicwrites import atomic_write
from twine.utils import DEFAULT_REPOSITORY, TEST_REPOSITORY

from hatch.build import build_package
from hatch.clean import clean_package, remove_compiled_scripts
from hatch.create import create_package
from hatch.env import (
    get_editable_package_location, get_installed_packages, get_python_version,
    get_python_implementation
)
from hatch.grow import BUMP, bump_package_version
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, load_settings, restore_settings,
    save_settings
)
from hatch.shells import IMMORTAL_SHELLS, get_default_shell_info, get_shell_command
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, ON_WINDOWS, basepath, chdir, get_proper_pip,
    get_proper_python, remove_path, venv_active
)
from hatch.venv import (
    VENV_DIR, clone_venv, create_venv, fix_available_venvs, get_available_venvs, venv
)


CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}
UNKNOWN_OPTIONS = {
    'ignore_unknown_options': True,
    **CONTEXT_SETTINGS
}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def hatch():
    pass


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help='Creates a new Python project')
@click.argument('name')
@click.option('--basic', is_flag=True,
              help='Disables CI/coverage services and readme badges.')
@click.option('--cli', is_flag=True,
              help=(
                  'Creates a `cli.py` in the package directory and an entry '
                  'point in `setup.py` pointing to the properly named function '
                  'within. Also, a `__main__.py` is created so it can be '
                  'invoked via `python -m pkg_name`.'
              ))
@click.option('-l', '--licenses',
              help='Comma-separated list of licenses to use. This overrides the config file.')
def egg(name, basic, cli, licenses):
    """Creates a new Python project.

    Values from your config file such as `name` and `pyversions` will be used
    to help populate fields. You can also specify things like the readme format
    and which CI service files to create.

    Here is an example using an unmodified config file:

    \b
    $ hatch egg my-app
    Created project `my-app`
    $ tree --dirsfirst my-app
    my-app
    ├── my_app
    │   └── __init__.py
    ├── tests
    │   └── __init__.py
    ├── LICENSE-APACHE
    ├── LICENSE-MIT
    ├── MANIFEST.in
    ├── README.rst
    ├── requirements.txt
    ├── setup.py
    └── tox.ini

    2 directories, 8 files
    """
    try:
        settings = load_settings()
    except FileNotFoundError:
        click.echo('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    if basic:
        settings['basic'] = True

    if licenses:
        settings['licenses'] = licenses.split(',')

    settings['cli'] = cli

    origin = os.getcwd()
    d = os.path.join(origin, name)

    if os.path.exists(d):
        click.echo('Directory `{}` already exists.'.format(d))
        sys.exit(1)

    os.makedirs(d)
    with chdir(d, cwd=origin):
        create_package(d, name, settings)
        click.echo('Created project `{}`'.format(name))


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help='Creates a new Python project in the current directory')
@click.argument('name')
@click.option('--basic', is_flag=True,
              help='Disables CI/coverage services and readme badges.')
@click.option('--cli', is_flag=True,
              help=(
                  'Creates a `cli.py` in the package directory and an entry '
                  'point in `setup.py` pointing to the properly named function '
                  'within. Also, a `__main__.py` is created so it can be '
                  'invoked via `python -m pkg_name`.'
              ))
@click.option('-l', '--licenses',
              help='Comma-separated list of licenses to use. This overrides the config file.')
def init(name, basic, cli, licenses):
    """Creates a new Python project in the current directory.

    Values from your config file such as `name` and `pyversions` will be used
    to help populate fields. You can also specify things like the readme format
    and which CI service files to create.

    Here is an example using an unmodified config file:

    \b
    $ hatch init my-app
    Created project `my-app` here
    $ tree --dirsfirst .
    .
    ├── my_app
    │   └── __init__.py
    ├── tests
    │   └── __init__.py
    ├── LICENSE-APACHE
    ├── LICENSE-MIT
    ├── MANIFEST.in
    ├── README.rst
    ├── requirements.txt
    ├── setup.py
    └── tox.ini

    2 directories, 8 files
    """
    try:
        settings = load_settings()
    except FileNotFoundError:
        click.echo('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    if basic:
        settings['basic'] = True

    if licenses:
        settings['licenses'] = licenses.split(',')

    settings['cli'] = cli

    create_package(os.getcwd(), name, settings)
    click.echo('Created project `{}` here'.format(name))


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help='Locates, updates, or restores the config file')
@click.option('-u', '--update', 'update_settings', is_flag=True,
              help='Updates the config file with any new fields.')
@click.option('--restore', is_flag=True,
              help='Restores the config file to default settings.')
def config(update_settings, restore):
    """Locates, updates, or restores the config file.

    \b
    $ hatch config
    Settings location: /home/ofek/.local/share/hatch/settings.json
    """
    if update_settings:
        try:
            user_settings = load_settings()
            updated_settings = copy_default_settings()
            updated_settings.update(user_settings)
            save_settings(updated_settings)
            click.echo('Settings were successfully updated.')
        except FileNotFoundError:
            restore = True

    if restore:
        restore_settings()
        click.echo('Settings were successfully restored.')

    click.echo('Settings location: ' + SETTINGS_FILE)


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Installs packages')
@click.argument('packages', nargs=-1)
@click.option('-e', '--env', 'env_name', help='The named virtual env to use.')
@click.option('-g', '--global', 'global_install', is_flag=True,
              help=(
                  'Installs globally, rather than on a per-user basis. This '
                  'has no effect if a virtual env is in use.'
              ))
def install(packages, env_name, global_install):
    """If the option --env is supplied, the update will be applied using
    that named virtual env. Unless the option --global is selected, the
    update will only affect the current user. Of course, this will have
    no effect if a virtual env is in use.

    With no packages selected, this will install using a `setup.py` in the
    current directory.
    """
    packages = packages or ['.']

    if env_name:
        venv_dir = os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            click.echo('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            command = [get_proper_pip(), 'install', *packages]
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    else:
        command = [get_proper_pip(), 'install']
        if not venv_active() and not global_install:  # no cov
            command.append('--user')
        command.extend(packages)

        result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)

    sys.exit(result.returncode)


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Updates packages')
@click.argument('packages', nargs=-1)
@click.option('-e', '--env', 'env_name', help='The named virtual env to use.')
@click.option('--eager', is_flag=True,
              help=(
                  'Updates all dependencies regardless of whether they '
                  'still satisfy the new parent requirements. See: '
                  'https://github.com/pypa/pip/pull/3972'
              ))
@click.option('--all', 'all_packages', is_flag=True,
              help=(
                  'Updates all currently installed packages. The packages '
                  '`pip`, `setuptools`, and `wheel` are excluded.'
              ))
@click.option('--infra', is_flag=True,
              help='Updates only the packages `pip`, `setuptools`, and `wheel`.')
@click.option('-g', '--global', 'global_install', is_flag=True,
              help=(
                  'Updates globally, rather than on a per-user basis. This '
                  'has no effect if a virtual env is in use.'
              ))
@click.option('-m', '--module', 'as_module', is_flag=True,
              help=(
                  'Invokes `pip` as a module instead of directly, i.e. '
                  '`python -m pip`.'
              ))
@click.option('--self', is_flag=True, help='Updates `hatch` itself')
def update(packages, env_name, eager, all_packages,
           infra, global_install, as_module, self):
    """If the option --env is supplied, the update will be applied using
    that named virtual env. Unless the option --global is selected, the
    update will only affect the current user. Of course, this will have
    no effect if a virtual env is in use.

    With no packages nor options selected, this will update packages by
    looking for a `requirements.txt` or a dev version of that in the current
    directory.

    To update this tool, use the --self flag. After the update, you may want
    to press Enter. All other methods of updating will ignore `hatch`. See:
    https://github.com/pypa/pip/issues/1299
    """
    temp_dir = None
    command = [
        'install', '--upgrade', '--upgrade-strategy',
        'eager' if eager else 'only-if-needed'
    ]
    infra_packages = ['pip', 'setuptools', 'wheel']

    if self:  # no cov
        as_module = True

    if env_name:
        venv_dir = os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            click.echo('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            executable = (
                [sys.executable if self else get_proper_python(), '-m', 'pip']
                if as_module or (infra and ON_WINDOWS)
                else [get_proper_pip()]
            )
            command = executable + command
            if all_packages:
                installed_packages = infra_packages if infra else get_installed_packages()
            else:
                installed_packages = None
    else:
        venv_dir = None
        executable = (
            [sys.executable if self else get_proper_python(), '-m', 'pip']
            if as_module or (infra and ON_WINDOWS)
            else [get_proper_pip()]
        )
        command = executable + command
        if all_packages:
            installed_packages = infra_packages if infra else get_installed_packages()
        else:
            installed_packages = None

        if not venv_active() and not global_install:  # no cov
            command.append('--user')

    if self:  # no cov
        command.append('hatch')
        if venv_dir:
            with venv(venv_dir):
                subprocess.Popen(command, shell=NEED_SUBPROCESS_SHELL)
        else:
            subprocess.Popen(command, shell=NEED_SUBPROCESS_SHELL)
        sys.exit()
    elif infra:
        command.extend(infra_packages)
    elif all_packages:
        installed_packages = [
            package for package in installed_packages
            if package not in infra_packages and package != 'hatch'
        ]
        if not installed_packages:
            click.echo('No packages installed.')
            sys.exit(1)
        command.extend(installed_packages)
    elif packages:
        packages = [package for package in packages if package != 'hatch']
        if not packages:
            click.echo('No packages to install.')
            sys.exit(1)
        command.extend(packages)

    # When https://github.com/pypa/pipfile is finalized, we'll use it.
    else:
        reqs = os.path.join(os.getcwd(), 'requirements.txt')
        if not os.path.exists(reqs):
            paths = glob.glob(os.path.join(os.getcwd(), '*requirements*.txt'))
            if not paths:
                click.echo('Unable to locate a requirements file.')
                sys.exit(1)
            reqs = paths[0]

        with open(reqs, 'r') as f:
            lines = f.readlines()

        matches = []
        for line in lines:
            match = re.match(r'^[^=<>]+', line.lstrip())
            if match and match.group(0) == 'hatch':
                matches.append(line)

        if matches:
            for line in matches:
                lines.remove(line)

            temp_dir = TemporaryDirectory()
            reqs = os.path.join(temp_dir.name, basepath(reqs))

            with open(reqs, 'w') as f:
                f.writelines(lines)

        command.extend(['-r', reqs])

    if venv_dir:
        with venv(venv_dir):
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    else:
        result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)

    if temp_dir is not None:
        temp_dir.cleanup()

    sys.exit(result.returncode)


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help="Increments a project's version")
@click.argument('part', type=click.Choice(BUMP.keys()))
@click.argument('package', required=False)
@click.option('-p', '--path', help='A relative or absolute path to a project.')
@click.option('--pre', 'pre_token',
              help='The token to use for `pre` part. This overrides config. Default: rc')
@click.option('--build', 'build_token',
              help='The token to use for `build` part. This overrides config. Default: build')
def grow(part, package, path, pre_token, build_token):
    """Increments a project's version number using semantic versioning.
    Valid choices for the part are `major`, `minor`, `patch` (`fix` alias),
    `pre`, and `build`.

    The path to the project is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `pip install -e`.
    2. The option --path, which can be a relative or absolute path.
    3. The current directory.

    The path, and every top level directory within, will be checked for a
    `__version__.py`, `__about__.py`, and `__init__.py`, in that order. The
    first encounter of a `__version__` variable that also appears to equal a
    version string will be updated. Probable package paths will be given
    precedence.

    The default tokens for the prerelease and build parts, `rc` and `build`
    respectively, can be altered via the options `--pre` and `--build`, or
    the config entry `semver`.

    \b
    $ git clone -q https://github.com/requests/requests && cd requests
    $ hatch grow build
    Updated /home/ofek/requests/requests/__version__.py
    2.18.4 -> 2.18.4+build.1
    $ hatch grow fix
    Updated /home/ofek/requests/requests/__version__.py
    2.18.4+build.1 -> 2.18.5
    $ hatch grow pre
    Updated /home/ofek/requests/requests/__version__.py
    2.18.5 -> 2.18.5-rc.1
    $ hatch grow minor
    Updated /home/ofek/requests/requests/__version__.py
    2.18.5-rc.1 -> 2.19.0
    $ hatch grow major
    Updated /home/ofek/requests/requests/__version__.py
    2.19.0 -> 3.0.0
    """
    if package:
        path = get_editable_package_location(package)
        if not path:
            click.echo('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        relative_path = os.path.join(os.getcwd(), basepath(path))
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.getcwd()

    try:
        settings = load_settings()
    except FileNotFoundError:
        settings = {}

    pre_token = pre_token or settings.get('semver', {}).get('pre')
    build_token = build_token or settings.get('semver', {}).get('build')

    f, old_version, new_version = bump_package_version(
        path, part, pre_token, build_token
    )

    if new_version:
        click.echo('Updated {}'.format(f))
        click.echo('{} -> {}'.format(old_version, new_version))
    else:
        if f:
            click.echo('Found init files:')
            for file in f:
                click.echo(file)
            click.echo('\nUnable to find a version specifier.')
            sys.exit(1)
        else:
            click.echo('No init files found.')
            sys.exit(1)


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Runs tests')
@click.argument('package', required=False)
@click.option('-p', '--path',
              help='A relative or absolute path to a project or test directory.')
@click.option('-c', '--cov', is_flag=True,
              help='Computes, then outputs coverage after testing.')
@click.option('-m', '--merge', is_flag=True,
              help=(
                  'If --cov, coverage will run using --parallel-mode '
                  'and combine the results.'
              ))
@click.option('-ta', '--test-args', default='',
              help=(
                  'Pass through to `pytest`, overriding defaults. Example: '
                  '`hatch test -ta "-k test_core.py -vv"`'
              ))
@click.option('-ca', '--cov-args',
              help=(
                  'Pass through to `coverage run`, overriding defaults. '
                  'Example: `hatch test -ca "--timid --pylib"`'
              ))
@click.option('-e', '--env-aware', is_flag=True,
              help=(
                  'Invokes `pytest` and `coverage` as modules instead of '
                  'directly, i.e. `python -m pytest`.'
              ))
def test(package, path, cov, merge, test_args, cov_args, env_aware):
    """Runs tests using `pytest`, optionally checking coverage.

    The path is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `pip install -e`.
    2. The option --path, which can be a relative or absolute path.
    3. The current directory.

    If the path points to a package, it should have a `tests` directory.

    \b
    $ git clone https://github.com/ofek/privy && cd privy
    $ hatch test -c
    ========================= test session starts ==========================
    platform linux -- Python 3.5.2, pytest-3.2.1, py-1.4.34, pluggy-0.4.0
    rootdir: /home/ofek/privy, inifile:
    plugins: xdist-1.20.0, mock-1.6.2, httpbin-0.0.7, forked-0.2, cov-2.5.1
    collected 10 items

    \b
    tests/test_privy.py ..........

    \b
    ====================== 10 passed in 4.34 seconds =======================

    \b
    Tests completed, checking coverage...

    \b
    Name                  Stmts   Miss Branch BrPart  Cover   Missing
    -----------------------------------------------------------------
    privy/__init__.py         1      0      0      0   100%
    privy/core.py            30      0      0      0   100%
    privy/utils.py           13      0      4      0   100%
    tests/__init__.py         0      0      0      0   100%
    tests/test_privy.py      57      0      0      0   100%
    -----------------------------------------------------------------
    TOTAL                   101      0      4      0   100%
    """
    if package:
        path = get_editable_package_location(package)
        if not path:
            click.echo('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        relative_path = os.path.join(os.getcwd(), basepath(path))
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.getcwd()

    python_cmd = [get_proper_python(), '-m'] if env_aware else []
    command = python_cmd.copy()

    if cov:
        command.extend(['coverage', 'run'])
        command.extend(
            cov_args.split() if cov_args is not None
            else (['--parallel-mode'] if merge else [])
        )
        command.append('-m')

    command.append('pytest')
    command.extend(test_args.split())

    try:  # no cov
        sys.stdout.fileno()
        testing = False
    except io.UnsupportedOperation:  # no cov
        testing = True

    # For testing we need to pipe because Click changes stdio streams.
    stdout = sys.stdout if not testing else subprocess.PIPE
    stderr = sys.stderr if not testing else subprocess.PIPE

    with chdir(path):
        output = b''

        test_result = subprocess.run(
            command,
            stdout=stdout, stderr=stderr,
            shell=NEED_SUBPROCESS_SHELL
        )
        output += test_result.stdout or b''
        output += test_result.stderr or b''

        if cov:
            click.echo('\nTests completed, checking coverage...\n')

            if merge:
                result = subprocess.run(
                    python_cmd + ['coverage', 'combine', '--append'],
                    stdout=stdout, stderr=stderr,
                    shell=NEED_SUBPROCESS_SHELL
                )
                output += result.stdout or b''
                output += result.stderr or b''

            result = subprocess.run(
                python_cmd + ['coverage', 'report', '--show-missing'],
                stdout=stdout, stderr=stderr,
                shell=NEED_SUBPROCESS_SHELL
            )
            output += result.stdout or b''
            output += result.stderr or b''

    if testing:  # no cov
        click.echo(output.decode())
        click.echo(output.decode())

    sys.exit(test_result.returncode)


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help="Removes a project's build artifacts")
@click.argument('package', required=False)
@click.option('-p', '--path', help='A relative or absolute path to a project.')
@click.option('-c', '--compiled-only', is_flag=True,
              help='Removes only .pyc files.')
@click.option('-v', '--verbose', is_flag=True, help='Shows removed paths.')
def clean(package, path, compiled_only, verbose):
    """Removes a project's build artifacts.

    The path to the project is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `pip install -e`.
    2. The option --path, which can be a relative or absolute path.
    3. The current directory.

    All `*.pyc`/`*.pyd` files and `__pycache__` directories will be removed.
    Additionally, the following patterns will be removed in the root of the
    path: `.cache`, `.coverage`, `.eggs`, `.tox`, `build`, `dist`, `*.egg-info`

    If the path was derived from the optional package argument, the pattern
    `*.egg-info` will not be applied so as to not break that installation.
    """
    if package:
        path = get_editable_package_location(package)
        if not path:
            click.echo('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        relative_path = os.path.join(os.getcwd(), basepath(path))
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.getcwd()

    if compiled_only:
        removed_paths = remove_compiled_scripts(path)
    else:
        removed_paths = clean_package(path, editable=package)

    if verbose:
        if removed_paths:
            click.echo('Removed paths:')
            for p in removed_paths:
                click.echo(p)


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Builds a project')
@click.argument('package', required=False)
@click.option('-p', '--path', help='A relative or absolute path to a project.')
@click.option('-py', '--python', 'pyname',
              help='The named Python path to use. This overrides --pypath.')
@click.option('-pp', '--pypath',
              help='An absolute path to a Python executable.')
@click.option('-u', '--universal', is_flag=True,
              help='Indicates compatibility with both Python 2 and 3.')
@click.option('-n', '--name',
              help='Forces a particular platform name, e.g. linux_x86_64.')
@click.option('-d', '--build-dir',
              help='An absolute path to the desired build directory.')
@click.option('-c', '--clean', 'clean_first', is_flag=True,
              help='Removes build artifacts before building.')
def build(package, path, pyname, pypath, universal, name, build_dir, clean_first):
    """Builds a project, producing a source distribution and a wheel.

    The path to the project is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `pip install -e`.
    2. The option --path, which can be a relative or absolute path.
    3. The current directory.

    The path must contain a `setup.py` file.
    """
    if package:
        path = get_editable_package_location(package)
        if not path:
            click.echo('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        relative_path = os.path.join(os.getcwd(), basepath(path))
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.getcwd()

    if pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:
            click.echo('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        pypath = settings.get('pythons', {}).get(pyname, None)
        if not pypath:
            click.echo('Python path named `{}` does not exist or is invalid.'.format(pyname))
            sys.exit(1)

    if clean_first:
        clean_package(path, editable=package)

    sys.exit(build_package(path, universal, name, build_dir, pypath))


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Uploads to PyPI')
@click.argument('package', required=False)
@click.option('-p', '--path',
              help='A relative or absolute path to a build directory.')
@click.option('-u', '--username', help='The PyPI username to use.')
@click.option('-t', '--test', 'test_pypi', is_flag=True,
              help='Uses the test version of PyPI.')
@click.option('-s', '--strict', is_flag=True,
              help='Aborts if a distribution already exists.')
def release(package, path, username, test_pypi, strict):
    """Uploads all files in a directory to PyPI.

    The path to the build directory is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `pip install -e`.
    2. The option --path, which can be a relative or absolute path.
    3. The current directory.

    If the path was derived from the optional package argument, the
    files must be in a directory named `dist`.
    """
    if package:
        path = get_editable_package_location(package)
        if not path:
            click.echo('`{}` is not an editable package.'.format(package))
            sys.exit(1)
        path = os.path.join(path, 'dist')
    elif path:
        relative_path = os.path.join(os.getcwd(), basepath(path))
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.getcwd()

    if not username:
        try:
            settings = load_settings()
        except FileNotFoundError:
            click.echo('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        username = settings.get('pypi_username', None)
        if not username:
            click.echo(
                'A username must be supplied via -u/--username or '
                'in {} as pypi_username.'.format(SETTINGS_FILE)
            )
            sys.exit(1)

    command = ['twine', 'upload', '{}{}*'.format(path, os.path.sep), '-u', username]

    if test_pypi:
        command.extend(['-r', TEST_REPOSITORY, '--repository-url', TEST_REPOSITORY])
    else:  # no cov
        command.extend(['-r', DEFAULT_REPOSITORY, '--repository-url', DEFAULT_REPOSITORY])

    if not strict:
        command.append('--skip-existing')

    result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    sys.exit(result.returncode)


def list_pythons(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    try:
        settings = load_settings()
    except FileNotFoundError:
        click.echo('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    pythons = settings.get('pythons', {})
    if pythons:
        for p in pythons:
            click.echo('{} -> {}'.format(p, pythons[p]))
    else:
        click.echo('There are no saved Python paths. Add '
                   'one via `hatch python NAME PATH`.')

    ctx.exit()


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('name')
@click.argument('path')
@click.option('-l', '--list', 'show', is_flag=True, is_eager=True, callback=list_pythons)
def python(name, path, show):
    try:
        settings = load_settings()
    except FileNotFoundError:
        click.echo('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    if 'pythons' not in settings:
        updated_settings = copy_default_settings()
        updated_settings.update(settings)
        settings = updated_settings
        click.echo('Settings were successfully updated to include `pythons` entry.')

    settings['pythons'][name] = path
    save_settings(settings)
    click.echo('Successfully saved Python `{}` located at `{}`.'.format(name, path))


def list_envs(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    venvs = get_available_venvs()

    if venvs:
        click.echo('Virtual environments found in {}:\n'.format(VENV_DIR))
        for venv_name, venv_dir in venvs:
            with venv(venv_dir):
                click.echo(
                    '{} ->\n'
                    '  Version: {}\n'
                    '  Implementation: {}'.format(
                        venv_name, get_python_version(), get_python_implementation()
                    )
                )

    # I don't want to move users' virtual environments
    # temporarily for tests as one may be in use.
    else:  # no cov
        click.echo('No virtual environments found in {}. To create '
                   'one do `hatch env NAME`.'.format(VENV_DIR))

    ctx.exit()


def restore_envs(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    fix_available_venvs()
    click.echo('Successfully restored all available virtual envs.')
    ctx.exit()


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('name')
@click.option('-p', '--python', 'pyname')
@click.option('-pp', '--pypath')
@click.option('-c', '--clone')
@click.option('-r', '--restore', is_flag=True, is_eager=True, callback=restore_envs)
@click.option('-l', '--list', 'show', is_flag=True, is_eager=True, callback=list_envs)
def env(name, pyname, pypath, clone, restore, show):
    if pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:
            click.echo('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        pypath = settings.get('pythons', {}).get(pyname, None)
        if not pypath:
            click.echo('Unable to find a Python path named `{}`.'.format(pyname))
            sys.exit(1)

    venv_dir = os.path.join(VENV_DIR, name)
    if os.path.exists(venv_dir):
        click.echo('Virtual env `{name}` already exists. To remove '
                   'it do `hatch shed -e {name}`.'.format(name=name))
        sys.exit(1)

    if not clone and not pyname and pypath and not os.path.exists(pypath):
        click.echo('Python path `{}` does not exist. Be sure to use the absolute path '
                   'e.g. `/usr/bin/python` instead of simply `python`.'.format(pypath))
        sys.exit(1)

    if clone:
        origin = os.path.join(VENV_DIR, clone)
        if not os.path.exists(origin):
            click.echo('Virtual env `{name}` does not exist.'.format(name=clone))
            sys.exit(1)
        clone_venv(origin, venv_dir)
        click.echo('Successfully cloned virtual env `{}` from `{}` to {}.'.format(name, clone, venv_dir))
    else:
        create_venv(venv_dir, pypath)
        click.echo('Successfully saved virtual env `{}` to `{}`.'.format(name, venv_dir))


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.option('-p', '--python', 'pyname')
@click.option('-e', '--env', 'env_name')
@click.pass_context
def shed(ctx, pyname, env_name):
    if not (pyname or env_name):
        click.echo(ctx.get_help())
        return

    if pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:
            click.echo('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        pypath = settings.get('pythons', {}).pop(pyname, None)
        if pypath is not None:
            click.echo('Successfully removed Python path named `{}`.'.format(pyname))
            save_settings(settings)
        else:
            click.echo('Python path named `{}` already does not exist.'.format(pyname))
    else:
        venv_dir = os.path.join(VENV_DIR, env_name)
        if os.path.exists(venv_dir):
            remove_path(venv_dir)
            click.echo('Successfully removed virtual env named `{}`.'.format(env_name))
        else:
            click.echo('Virtual env named `{}` already does not exist.'.format(env_name))


@hatch.command(context_settings=UNKNOWN_OPTIONS)
@click.argument('env_name')
@click.argument('command', required=False, nargs=-1, type=click.UNPROCESSED)
@click.option('-s', '--shell')
@click.option('--nest/--kill', '-n/-k', default=None)
def use(env_name, command, shell, nest):  # no cov

    # Run commands regardless of virtual env activation.
    if command:
        venv_dir = os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            click.echo('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        result = None
        try:
            with venv(venv_dir):
                result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
        finally:
            sys.exit(1 if result is None else result.returncode)

    try:
        settings = load_settings()
    except FileNotFoundError:
        settings = {}

    shell_name, shell_path = get_default_shell_info(shell, settings)

    if shell_name in IMMORTAL_SHELLS or nest or (nest is None and settings.get('nest_shells')):
        venv_dir = os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            click.echo('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            with get_shell_command(env_name, shell_name, shell_path, nest=True) as shell_command:
                subprocess.run(shell_command, shell=NEED_SUBPROCESS_SHELL)
        return

    # If in activated venv shell, notify main loop and exit.
    if '_HATCH_FILE_' in os.environ:
        with atomic_write(os.environ['_HATCH_FILE_'], overwrite=True) as f:
            data = json.dumps({
                'env_name': env_name,
                'shell': shell
            })
            f.write(data)
        return

    with TemporaryDirectory() as d:
        communication_file = os.path.join(d, 'temp.json')
        evars = {'_HATCH_FILE_': communication_file}

        while True:
            venv_dir = os.path.join(VENV_DIR, env_name)
            if not os.path.exists(venv_dir):
                click.echo('Virtual env named `{}` does not exist.'.format(env_name))
                sys.exit(1)

            shell_name, shell_path = get_default_shell_info(shell)

            with venv(venv_dir, evars=evars):
                try:
                    with get_shell_command(env_name, shell_name, shell_path) as shell_command:
                        process = subprocess.Popen(shell_command)
                        while True:
                            if process.poll() is not None:
                                return

                            if os.path.exists(communication_file):

                                # This is necessary on non-Windows machines.
                                #
                                # Killing a spawned shell suspends execution of
                                # this script due to competition for terminal use.
                                # Termination works, however only if the spawned
                                # shell has no active processes. Therefore, we sleep
                                # shortly to ensure the second `hatch use ...` has
                                # time to write the communication file and exit.
                                if not ON_WINDOWS:
                                    time.sleep(0.2)

                                with open(communication_file, 'r') as f:
                                    args = json.loads(f.read())
                                env_name = args['env_name']
                                shell = args['shell']

                                remove_path(communication_file)
                                process.terminate()
                                break
                except KeyboardInterrupt:
                    break










