import io
import os
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

import click
from twine.utils import DEFAULT_REPOSITORY, TEST_REPOSITORY

from hatch.build import build_package
from hatch.clean import clean_package, remove_compiled_scripts
from hatch.create import create_package
from hatch.env import (
    get_editable_packages, get_editable_package_location, get_installed_packages,
    get_python_version, get_python_implementation, install_packages
)
from hatch.grow import BUMP, bump_package_version
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, load_settings, restore_settings,
    save_settings
)
from hatch.shells import run_shell
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, ON_WINDOWS, basepath, chdir, get_admin_command,
    get_proper_pip, get_proper_python, get_random_venv_name, get_requirements_file,
    remove_path, resolve_path, venv_active
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


def echo_success(text):
    click.secho(text, fg='cyan', bold=True)


def echo_failure(text):
    click.secho(text, fg='red', bold=True)


def echo_warning(text):
    click.secho(text, fg='yellow', bold=True)


def echo_waiting(text):
    click.secho(text, fg='magenta', bold=True)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def hatch():
    pass


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
            echo_success('Settings were successfully updated.')
        except FileNotFoundError:
            restore = True

    if restore:
        restore_settings()
        echo_success('Settings were successfully restored.')

    echo_success('Settings location: ' + SETTINGS_FILE)


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help='Creates a new Python project')
@click.argument('name')
@click.argument('new_env', required=False)
@click.option('-e', '--env', 'env_name',
              help=(
                  'Forward-slash-separated list of named virtual envs to be '
                  "installed in. Will create any that don't already exist."
              ))
@click.option('--basic', is_flag=True,
              help='Disables third-party services and readme badges.')
@click.option('--cli', is_flag=True,
              help=(
                  'Creates a `cli.py` in the package directory and an entry '
                  'point in `setup.py` pointing to the properly named function '
                  'within. Also, a `__main__.py` is created so it can be '
                  'invoked via `python -m pkg_name`.'
              ))
@click.option('-l', '--licenses',
              help='Comma-separated list of licenses to use.')
def new(name, new_env, env_name, basic, cli, licenses):
    """Creates a new Python project.

    Values from your config file such as `name` and `pyversions` will be used
    to help populate fields. You can also specify things like the readme format
    and which CI service files to create. All options override the config file.

    You can also locally install the created project in a virtual env using
    the optional argument or the --env option. If the virtual env for the
    optional argument already exists, an error will be raised.

    Here is an example using an unmodified config file:

    \b
    $ hatch new my-app
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
        echo_failure('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    venvs = env_name.split('/') if env_name else []
    if new_env:
        venv_dir = os.path.join(VENV_DIR, new_env)
        if os.path.exists(venv_dir):
            echo_failure('Virtual env `{name}` already exists. To remove '
                         'it do `hatch shed -e {name}`.'.format(name=new_env))
            sys.exit(1)
        venvs.insert(0, new_env)

    if basic:
        settings['basic'] = True

    if licenses:
        settings['licenses'] = licenses.split(',')

    settings['cli'] = cli

    origin = os.getcwd()
    d = os.path.join(origin, name)

    if os.path.exists(d):
        echo_failure('Directory `{}` already exists.'.format(d))
        sys.exit(1)

    os.makedirs(d)
    with chdir(d, cwd=origin):
        create_package(d, name, settings)
        echo_success('Created project `{}`'.format(name))

        for vname in venvs:
            venv_dir = os.path.join(VENV_DIR, vname)
            if not os.path.exists(venv_dir):
                echo_waiting('Creating virtual env `{}`...'.format(vname))
                create_venv(venv_dir)

            with venv(venv_dir):
                echo_waiting('Installing locally in virtual env `{}`...'.format(vname))
                install_packages(['-q', '-e', '.'])


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help='Creates a new Python project in the current directory')
@click.argument('name')
@click.argument('new_env', required=False)
@click.option('-e', '--env', 'env_name',
              help=(
                  'Forward-slash-separated list of named virtual envs to be '
                  "installed in. Will create any that don't already exist."
              ))
@click.option('--basic', is_flag=True,
              help='Disables third-party services and readme badges.')
@click.option('--cli', is_flag=True,
              help=(
                  'Creates a `cli.py` in the package directory and an entry '
                  'point in `setup.py` pointing to the properly named function '
                  'within. Also, a `__main__.py` is created so it can be '
                  'invoked via `python -m pkg_name`.'
              ))
@click.option('-l', '--licenses',
              help='Comma-separated list of licenses to use.')
def init(name, new_env, env_name, basic, cli, licenses):
    """Creates a new Python project in the current directory.

    Values from your config file such as `name` and `pyversions` will be used
    to help populate fields. You can also specify things like the readme format
    and which CI service files to create. All options override the config file.

    You can also locally install the created project in a virtual env using
    the optional argument or the --env option. If the virtual env for the
    optional argument already exists, an error will be raised.

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
        echo_failure('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    venvs = env_name.split('/') if env_name else []
    if new_env:
        venv_dir = os.path.join(VENV_DIR, new_env)
        if os.path.exists(venv_dir):
            echo_failure('Virtual env `{name}` already exists. To remove '
                         'it do `hatch shed -e {name}`.'.format(name=new_env))
            sys.exit(1)
        venvs.insert(0, new_env)

    if basic:
        settings['basic'] = True

    if licenses:
        settings['licenses'] = licenses.split(',')

    settings['cli'] = cli

    create_package(os.getcwd(), name, settings)
    echo_success('Created project `{}` here'.format(name))

    for vname in venvs:
        venv_dir = os.path.join(VENV_DIR, vname)
        if not os.path.exists(venv_dir):
            echo_waiting('Creating virtual env `{}`...'.format(vname))
            create_venv(venv_dir)

        with venv(venv_dir):
            echo_waiting('Installing locally in virtual env `{}`...'.format(vname))
            install_packages(['-q', '-e', '.'])


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Installs packages')
@click.argument('packages', nargs=-1)
@click.option('-e', '--env', 'env_name', help='The named virtual env to use.')
@click.option('-l', '--local', 'editable', is_flag=True,
              help=(
                  "Corresponds to pip's --editable option, allowing a local "
                  "package to be automatically updated when modifications "
                  "are made."
              ))
@click.option('-g', '--global', 'global_install', is_flag=True,
              help=(
                  'Installs globally, rather than on a per-user basis. This '
                  'has no effect if a virtual env is in use.'
              ))
@click.option('-q', '--quiet', is_flag=True, help='Decreases verbosity.')
def install(packages, env_name, editable, global_install, quiet):
    """If the option --env is supplied, the install will be applied using
    that named virtual env. Unless the option --global is selected, the
    install will only affect the current user. Of course, this will have
    no effect if a virtual env is in use. The desired name of the admin
    user can be set with the `_DEFAULT_ADMIN_` environment variable.

    With no packages selected, this will install using a `setup.py` in the
    current directory.
    """
    packages = packages or ['.']

    # Windows' `runas` allows only a single argument for the
    # command so we catch this case and turn our command into
    # a string later.
    windows_admin_command = None

    if editable:
        packages = ['-e', *packages]

    if env_name:
        venv_dir = os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            echo_failure('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            command = [get_proper_pip(), 'install', *packages] + (['-q'] if quiet else [])
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    else:
        command = [get_proper_pip(), 'install'] + (['-q'] if quiet else [])

        if not venv_active():  # no cov
            if global_install:
                if ON_WINDOWS:
                    windows_admin_command = get_admin_command()
                else:
                    command = get_admin_command() + command
            else:
                command.append('--user')

        command.extend(packages)

        if windows_admin_command:  # no cov
            command = windows_admin_command + [' '.join(command)]

        result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)

    sys.exit(result.returncode)


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Uninstalls packages')
@click.argument('packages', nargs=-1)
@click.option('-e', '--env', 'env_name', help='The named virtual env to use.')
@click.option('-g', '--global', 'global_uninstall', is_flag=True,
              help=(
                  'Uninstalls globally, rather than on a per-user basis. This '
                  'has no effect if a virtual env is in use.'
              ))
@click.option('-d', '--dev', is_flag=True,
              help='When locating a requirements file, only use the dev version.')
@click.option('-q', '--quiet', is_flag=True, help='Decreases verbosity.')
@click.option('-y', '--yes', is_flag=True,
              help='Confirms the intent to uninstall without a prompt.')
def uninstall(packages, env_name, global_uninstall, dev, quiet, yes):
    """If the option --env is supplied, the uninstall will be applied using
    that named virtual env. Unless the option --global is selected, the
    uninstall will only affect the current user. Of course, this will have
    no effect if a virtual env is in use. The desired name of the admin
    user can be set with the `_DEFAULT_ADMIN_` environment variable.

    With no packages selected, this will uninstall using a `requirements.txt`
    or a dev version of that in the current directory.
    """
    if not packages:
        reqs = get_requirements_file(os.getcwd(), dev=dev)
        if not reqs:
            echo_failure('Unable to locate a requirements file.')
            sys.exit(1)

        packages = ['-r', reqs]

    # Windows' `runas` allows only a single argument for the
    # command so we catch this case and turn our command into
    # a string later.
    windows_admin_command = None

    if yes:  # no cov
        packages = ['-y', *packages]

    if env_name:
        venv_dir = os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            echo_failure('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            command = [get_proper_pip(), 'uninstall', *packages] + (['-q'] if quiet else [])
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    else:
        command = [get_proper_pip(), 'uninstall'] + (['-q'] if quiet else [])

        if not venv_active() and global_uninstall:  # no cov
            if ON_WINDOWS:
                windows_admin_command = get_admin_command()
            else:
                command = get_admin_command() + command

        command.extend(packages)

        if windows_admin_command:  # no cov
            command = windows_admin_command + [' '.join(command)]

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
@click.option('-f', '--force', is_flag=True,
              help='Forces the use of newer features in global updates.')
@click.option('-d', '--dev', is_flag=True,
              help='When locating a requirements file, only use the dev version.')
@click.option('-m', '--module', 'as_module', is_flag=True,
              help=(
                  'Invokes `pip` as a module instead of directly, i.e. '
                  '`python -m pip`.'
              ))
@click.option('--self', is_flag=True, help='Updates `hatch` itself.')
@click.option('-q', '--quiet', is_flag=True, help='Decreases verbosity.')
def update(packages, env_name, eager, all_packages, infra, global_install,
           force, dev, as_module, self, quiet):
    """If the option --env is supplied, the update will be applied using
    that named virtual env. Unless the option --global is selected, the
    update will only affect the current user. Of course, this will have
    no effect if a virtual env is in use. The desired name of the admin
    user can be set with the `_DEFAULT_ADMIN_` environment variable.

    When performing a global update, your system may use an older version
    of pip that is incompatible with some features such as --eager. To
    force the use of these features, use --force.

    With no packages nor options selected, this will update packages by
    looking for a `requirements.txt` or a dev version of that in the current
    directory.

    To update this tool, use the --self flag. On Windows, you may want to
    press Enter after the self update. All other methods of updating will
    ignore `hatch`. See: https://github.com/pypa/pip/issues/1299
    """
    command = ['install', '--upgrade'] + (['-q'] if quiet else [])
    if not global_install or force:  # no cov
        command.extend(['--upgrade-strategy', 'eager' if eager else 'only-if-needed'])

    infra_packages = ['pip', 'setuptools', 'wheel']
    temp_dir = None

    # Windows' `runas` allows only a single argument for the
    # command so we catch this case and turn our command into
    # a string later.
    windows_admin_command = None

    if self:  # no cov
        as_module = True

    if env_name and not self:
        venv_dir = os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            echo_failure('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            executable = (
                [get_proper_python(), '-m', 'pip']
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

        if not venv_active():  # no cov
            if global_install:
                if ON_WINDOWS:
                    windows_admin_command = get_admin_command()
                else:
                    command = get_admin_command() + command
            else:
                command.append('--user')

    if self:  # no cov
        command.append('hatch')
        if ON_WINDOWS:
            subprocess.Popen(command, shell=NEED_SUBPROCESS_SHELL)
            sys.exit()
        else:
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
            sys.exit(result.returncode)
    elif infra:
        command.extend(infra_packages)
    elif all_packages:
        installed_packages = [
            package for package in installed_packages
            if package not in infra_packages and package != 'hatch'
        ]
        if not installed_packages:
            echo_failure('No packages installed.')
            sys.exit(1)
        command.extend(installed_packages)
    elif packages:
        packages = [package for package in packages if package != 'hatch']
        if not packages:
            echo_failure('No packages to install.')
            sys.exit(1)
        command.extend(packages)

    # When https://github.com/pypa/pipfile is finalized, we'll use it.
    else:
        reqs = get_requirements_file(os.getcwd(), dev=dev)
        if not reqs:
            echo_failure('Unable to locate a requirements file.')
            sys.exit(1)

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

    if windows_admin_command:  # no cov
        command = windows_admin_command + [' '.join(command)]

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
@click.option('-p', '--path', help='A relative or absolute path to a project or file.')
@click.option('--pre', 'pre_token',
              help='The token to use for `pre` part, overriding the config file. Default: rc')
@click.option('--build', 'build_token',
              help='The token to use for `build` part, overriding the config file. Default: build')
def grow(part, package, path, pre_token, build_token):
    """Increments a project's version number using semantic versioning.
    Valid choices for the part are `major`, `minor`, `patch` (`fix` alias),
    `pre`, and `build`.

    The path to the project is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `hatch install -l` or `pip install -e`.
    2. The option --path, which can be a relative or absolute path.
    3. The current directory.

    If the path is a file, it will be the target. Otherwise, the path, and
    every top level directory within, will be checked for a `__version__.py`,
    `__about__.py`, and `__init__.py`, in that order. The first encounter of
    a `__version__` variable that also appears to equal a version string will
    be updated. Probable package paths will be given precedence.

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
            echo_failure('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        possible_path = resolve_path(path)
        if not possible_path:
            echo_failure('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
        path = possible_path
    else:
        path = os.getcwd()

    settings = load_settings(lazy=True)
    pre_token = pre_token or settings.get('semver', {}).get('pre')
    build_token = build_token or settings.get('semver', {}).get('build')

    f, old_version, new_version = bump_package_version(
        path, part, pre_token, build_token
    )

    if new_version:
        echo_success('Updated {}'.format(f))
        echo_success('{} -> {}'.format(old_version, new_version))
    else:
        if f:
            echo_failure('Found version files:')
            for file in f:
                echo_failure(file)
                echo_failure('\nUnable to find a version specifier.')
            sys.exit(1)
        else:
            echo_failure('No version files found.')
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
       that was installed via `hatch install -l` or `pip install -e`.
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
            echo_failure('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        possible_path = resolve_path(path)
        if not possible_path:
            echo_failure('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
        path = possible_path
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
       that was installed via `hatch install -l` or `pip install -e`.
    2. The option --path, which can be a relative or absolute path.
    3. The current directory.

    All `*.pyc`/`*.pyd` files and `__pycache__` directories will be removed.
    Additionally, the following patterns will be removed from the root of the path:
    `.cache`, `.coverage`, `.eggs`, `.tox`, `build`, `dist`, and `*.egg-info`.

    If the path was derived from the optional package argument, the pattern
    `*.egg-info` will not be applied so as to not break that installation.
    """
    if package:
        path = get_editable_package_location(package)
        if not path:
            echo_failure('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        possible_path = resolve_path(path)
        if not possible_path:
            echo_failure('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
        path = possible_path
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
              help='A relative or absolute path to the desired build directory.')
@click.option('-c', '--clean', 'clean_first', is_flag=True,
              help='Removes build artifacts before building.')
@click.option('-v', '--verbose', is_flag=True, help='Increases verbosity.')
def build(package, path, pyname, pypath, universal, name, build_dir,
          clean_first, verbose):
    """Builds a project, producing a source distribution and a wheel.

    The path to the project is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `hatch install -l` or `pip install -e`.
    2. The option --path, which can be a relative or absolute path.
    3. The current directory.

    The path must contain a `setup.py` file.
    """
    if package:
        path = get_editable_package_location(package)
        if not path:
            echo_failure('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        possible_path = resolve_path(path)
        if not possible_path:
            echo_failure('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
        path = possible_path
    else:
        path = os.getcwd()

    if build_dir:
        build_dir = os.path.abspath(build_dir)
    else:
        build_dir = os.path.join(path, 'dist')

    if pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:
            echo_failure('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        pypath = settings.get('pypaths', {}).get(pyname, None)
        if not pypath:
            echo_failure('Python path named `{}` does not exist or is invalid.'.format(pyname))
            sys.exit(1)

    if clean_first:
        clean_package(path, editable=package)

    return_code = build_package(path, build_dir, universal, name, pypath, verbose)

    if os.path.isdir(build_dir):
        echo_success('Files found in `{}`:\n'.format(build_dir))
        for file in sorted(os.listdir(build_dir)):
            if os.path.isfile(os.path.join(build_dir, file)):
                click.echo(file)

    sys.exit(return_code)


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
    """Uploads all files in a directory to PyPI using Twine.

    The path to the build directory is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `hatch install -l` or `pip install -e`.
    2. The option --path, which can be a relative or absolute path.
    3. The current directory. If the current directory has a `dist`
       directory, that will be used instead.

    If the path was derived from the optional package argument, the
    files must be in a directory named `dist`.

    The PyPI username can be saved in the config file entry `pypi_username`.
    If the `TWINE_PASSWORD` environment variable is not set, a hidden prompt
    will be provided for the password.
    """
    if package:
        path = get_editable_package_location(package)
        if not path:
            echo_failure('`{}` is not an editable package.'.format(package))
            sys.exit(1)
        path = os.path.join(path, 'dist')
    elif path:
        possible_path = resolve_path(path)
        if not possible_path:
            echo_failure('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
        path = possible_path
    else:
        path = os.getcwd()
        default_build_dir = os.path.join(path, 'dist')
        if os.path.isdir(default_build_dir):
            path = default_build_dir

    if not username:
        try:
            settings = load_settings()
        except FileNotFoundError:
            echo_failure('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        username = settings.get('pypi_username', None)
        if not username:
            echo_failure(
                'A username must be supplied via -u/--username or '
                'in {} as pypi_username.'.format(SETTINGS_FILE)
            )
            sys.exit(1)

    command = [sys.executable, '-m', 'twine', 'upload', '-u', username,
               '{}{}*'.format(path, os.path.sep)]

    if test_pypi:
        command.extend(['-r', TEST_REPOSITORY, '--repository-url', TEST_REPOSITORY])
    else:  # no cov
        command.extend(['-r', DEFAULT_REPOSITORY, '--repository-url', DEFAULT_REPOSITORY])

    if not strict:
        command.append('--skip-existing')

    result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    sys.exit(result.returncode)


def list_pypaths(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    try:
        settings = load_settings()
    except FileNotFoundError:
        echo_failure('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    pypaths = settings.get('pypaths', {})
    if pypaths:
        for p in pypaths:
            echo_success('{} -> {}'.format(p, pypaths[p]))
    else:
        echo_failure('There are no saved Python paths. Add '
                     'one via `hatch pypath NAME PATH`.')

    ctx.exit()


@hatch.command('pypath', context_settings=CONTEXT_SETTINGS,
               short_help='Names a Python path or shows available ones')
@click.argument('name')
@click.argument('path')
@click.option('-l', '--list', 'show', is_flag=True, is_eager=True, callback=list_pypaths,
              help='Shows available Python paths.')
def python_path(name, path, show):
    """Names an absolute path to a Python executable. You can also modify
    these in the config file entry `pypaths`.

    Hatch can then use these paths by name when creating virtual envs, building
    packages, etc.

    \b
    $ hatch pypath -l
    There are no saved Python paths. Add one via `hatch pypath NAME PATH`.
    $ hatch pypath py2 /usr/bin/python
    Successfully saved Python `py2` located at `/usr/bin/python`.
    $ hatch pypath py3 /usr/bin/python3
    Successfully saved Python `py3` located at `/usr/bin/python3`.
    $ hatch pypath -l
    py2 -> /usr/bin/python
    py3 -> /usr/bin/python3
    """
    try:
        settings = load_settings()
    except FileNotFoundError:
        echo_failure('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    if 'pypaths' not in settings:
        updated_settings = copy_default_settings()
        updated_settings.update(settings)
        settings = updated_settings
        echo_success('Settings were successfully updated to include `pypaths` entry.')

    settings['pypaths'][name] = path
    save_settings(settings)
    echo_success('Successfully saved Python `{}` located at `{}`.'.format(name, path))


def list_envs(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    venvs = get_available_venvs()

    if venvs:
        echo_success('Virtual environments found in `{}`:\n'.format(VENV_DIR))
        for venv_name, venv_dir in venvs:
            with venv(venv_dir):
                echo_success('{} ->'.format(venv_name))
                if value == 1:
                    echo_success('  Version: {}'.format(get_python_version()))
                elif value == 2:
                    echo_success('  Version: {}'.format(get_python_version()))
                    echo_success('  Implementation: {}'.format(get_python_implementation()))
                else:
                    echo_success('  Version: {}'.format(get_python_version()))
                    echo_success('  Implementation: {}'.format(get_python_implementation()))
                    echo_success('  Local packages: {}'.format(', '.join(sorted(get_editable_packages()))))

    # I don't want to move users' virtual environments
    # temporarily for tests as one may be in use.
    else:  # no cov
        echo_failure('No virtual environments found in `{}`. To create '
                     'one do `hatch env NAME`.'.format(VENV_DIR))

    ctx.exit()


def restore_envs(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    fix_available_venvs()
    echo_success('Successfully restored all available virtual envs.')
    ctx.exit()


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help='Manages virtual environments')
@click.argument('name')
@click.option('-py', '--python', 'pyname',
              help='The named Python path to use. This overrides --pypath.')
@click.option('-pp', '--pypath',
              help='An absolute path to a Python executable.')
@click.option('-c', '--clone',
              help='Specifies an existing virtual env to clone. (Experimental)')
@click.option('-v', '--verbose', is_flag=True, help='Increases verbosity.')
@click.option('-r', '--restore', is_flag=True, is_eager=True, callback=restore_envs,
              help=(
                  'Attempts to make all virtual envs in `{}` usable by '
                  'fixing the executable paths in scripts and removing '
                  'all compiled `*.pyc` files. (Experimental)'.format(VENV_DIR)
              ))
@click.option('-l', '--list', 'show', count=True, is_eager=True, callback=list_envs,
              help=(
                  'Shows available virtual envs. Can stack up to 3 times to '
                  'show more info.'
              ))
def env(name, pyname, pypath, clone, verbose, restore, show):
    """Creates a new virtual env that can later be utilized with the
    `use` command.

    \b
    $ hatch pypath -l
    py2 -> /usr/bin/python
    py3 -> /usr/bin/python3
    $ hatch env -l
    No virtual environments found in /home/ofek/.virtualenvs. To create one do `hatch env NAME`.
    $ hatch env my-app
    Already using interpreter /usr/bin/python3
    Successfully saved virtual env `my-app` to `/home/ofek/.virtualenvs/my-app`.
    $ hatch env -py py2 old
    Successfully saved virtual env `old` to `/home/ofek/.virtualenvs/old`.
    $ hatch env -pp ~/pypy3/bin/pypy fast
    Successfully saved virtual env `fast` to `/home/ofek/.virtualenvs/fast`.
    $ hatch env -ll
    Virtual environments found in /home/ofek/.virtualenvs:

    \b
    fast ->
      Version: 3.5.3
      Implementation: PyPy
    my-app ->
      Version: 3.5.2
      Implementation: CPython
    old ->
      Version: 2.7.12
      Implementation: CPython
    """
    if pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:
            echo_failure('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        pypath = settings.get('pypaths', {}).get(pyname, None)
        if not pypath:
            echo_failure('Unable to find a Python path named `{}`.'.format(pyname))
            sys.exit(1)

    venv_dir = os.path.join(VENV_DIR, name)
    if os.path.exists(venv_dir):
        echo_failure('Virtual env `{name}` already exists. To remove '
                     'it do `hatch shed -e {name}`.'.format(name=name))
        sys.exit(1)

    if not clone and not pyname and pypath and not os.path.exists(pypath):
        echo_failure('Python path `{}` does not exist. Be sure to use the absolute path '
                     'e.g. `/usr/bin/python` instead of simply `python`.'.format(pypath))
        sys.exit(1)

    if clone:
        origin = os.path.join(VENV_DIR, clone)
        if not os.path.exists(origin):
            echo_failure('Virtual env `{name}` does not exist.'.format(name=clone))
            sys.exit(1)
        echo_waiting('Cloning virtual env `{}`...'.format(clone))
        clone_venv(origin, venv_dir)
        echo_success('Successfully cloned virtual env `{}` from `{}` to `{}`.'.format(name, clone, venv_dir))
    else:
        echo_waiting('Creating virtual env `{}`...'.format(name))
        create_venv(venv_dir, pypath, verbose=verbose)
        echo_success('Successfully saved virtual env `{}` to `{}`.'.format(name, venv_dir))


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help='Removes named Python paths or virtual environments')
@click.option('-p', '-py', '--pypath', 'pyname',
              help='Forward-slash-separated list of named Python paths.')
@click.option('-e', '--env', 'env_name',
              help='Forward-slash-separated list of named virtual envs.')
@click.pass_context
def shed(ctx, pyname, env_name):
    """Removes named Python paths or virtual environments.

    \b
    $ hatch pypath -l
    py2 -> /usr/bin/python
    py3 -> /usr/bin/python3
    invalid -> :\/:
    $ hatch env -ll
    Virtual environments found in /home/ofek/.virtualenvs:

    \b
    duplicate ->
      Version: 3.5.2
      Implementation: CPython
    fast ->
      Version: 3.5.3
      Implementation: PyPy
    my-app ->
      Version: 3.5.2
      Implementation: CPython
    old ->
      Version: 2.7.12
      Implementation: CPython
    $ hatch shed -p invalid -e duplicate/old
    Successfully removed Python path named `invalid`.
    Successfully removed virtual env named `duplicate`.
    Successfully removed virtual env named `old`.
    """
    if not (pyname or env_name):
        click.echo(ctx.get_help())
        return

    if pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:
            echo_failure('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        for pyname in pyname.split('/'):
            pypath = settings.get('pypaths', {}).pop(pyname, None)
            if pypath is not None:
                save_settings(settings)
                echo_success('Successfully removed Python path named `{}`.'.format(pyname))
            else:
                echo_warning('Python path named `{}` already does not exist.'.format(pyname))

    if env_name:
        for env_name in env_name.split('/'):
            venv_dir = os.path.join(VENV_DIR, env_name)
            if os.path.exists(venv_dir):
                remove_path(venv_dir)
                echo_success('Successfully removed virtual env named `{}`.'.format(env_name))
            else:
                echo_warning('Virtual env named `{}` already does not exist.'.format(env_name))


@hatch.command(context_settings=UNKNOWN_OPTIONS,
               short_help='Activates or sends a command to a virtual environment')
@click.argument('env_name', required=False)
@click.argument('command', required=False, nargs=-1, type=click.UNPROCESSED)
@click.option('-t', '--temp', 'temp_env', is_flag=True,
              help='Use a new temporary virtual env.')
@click.option('-s', '--shell',
              help=(
                  'The name of shell to use e.g. `bash`. If the shell name '
                  'is not supported, e.g. `bash -O`, it will be treated as '
                  'a command and no custom prompt will be provided. This '
                  'overrides the config file entry `shell`.'
              ))
@click.pass_context
def use(ctx, env_name, command, temp_env, shell):  # no cov
    """Activates or sends a command to a virtual environment. A default shell
    name (or command) can be specified in the config file entry `shell` or the
    environment variable `SHELL`. If there is no entry, env var, nor shell
    option provided, a system default will be used: `cmd` on Windows, `bash`
    otherwise.

    Any arguments provided after the first will be sent to the virtual env as
    a command without activating it. If there is only the env without args,
    it will be activated similarly to how you are accustomed. The name of
    the virtual env to use must be omitted if using the --temp env option.

    Activation will not do anything to your current shell, but will rather
    spawn a subprocess to avoid any unwanted strangeness occurring in your
    current environment. If you would like to learn more about the benefits
    of this approach, be sure to read https://gist.github.com/datagrok/2199506.
    To leave a virtual env, type `exit`, or you can do `Ctrl+D` on non-Windows
    machines.

    \b
    Activation:
    $ hatch env -ll
    Virtual environments found in `/home/ofek/.virtualenvs`:

    \b
    fast ->
      Version: 3.5.3
      Implementation: PyPy
    my-app ->
      Version: 3.5.2
      Implementation: CPython
    old ->
      Version: 2.7.12
      Implementation: CPython
    $ which python
    /usr/bin/python
    $ hatch use my-app
    (my-app) $ which python
    /home/ofek/.virtualenvs/my-app/bin/python

    \b
    Commands:
    $ hatch use my-app pip list --format=columns
    Package    Version
    ---------- -------
    pip        9.0.1
    setuptools 36.3.0
    wheel      0.29.0
    $ hatch use my-app hatch install -q requests six
    $ hatch use my-app pip list --format=columns
    Package    Version
    ---------- -----------
    certifi    2017.7.27.1
    chardet    3.0.4
    idna       2.6
    pip        9.0.1
    requests   2.18.4
    setuptools 36.3.0
    six        1.10.0
    urllib3    1.22
    wheel      0.29.0

    \b
    Temporary env:
    $ hatch use -t
    Already using interpreter /usr/bin/python3
    Using base prefix '/usr'
    New python executable in /tmp/tmpzg73untp/Ihqd/bin/python3
    Also creating executable in /tmp/tmpzg73untp/Ihqd/bin/python
    Installing setuptools, pip, wheel...done.
    $ which python
    /tmp/tmpzg73untp/Ihqd/bin/python
    """
    if not (env_name or temp_env):
        click.echo(ctx.get_help())
        return

    if env_name and temp_env:
        echo_failure('Cannot use more than one virtual env at a time!')
        sys.exit(1)

    if not command and '_HATCHING_' in os.environ:
        echo_failure(
            'Virtual environments cannot be nested, sorry! To leave '
            'the current one type `exit` or press `Ctrl+D`.'
        )
        sys.exit(1)

    if temp_env:
        temp_dir = TemporaryDirectory()
        env_name = get_random_venv_name()
        venv_dir = os.path.join(temp_dir.name, env_name)
        echo_waiting('Creating a temporary virtual env named `{}`...'.format(env_name))
        create_venv(venv_dir, verbose=True)
    else:
        temp_dir = None
        venv_dir = os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            echo_failure('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

    result = None

    try:
        if command:
            with venv(venv_dir):
                echo_waiting('Running `{}` in `{}`...'.format(
                    ' '.join(c if len(c.split()) == 1 else '"{}"'.format(c) for c in command),
                    env_name
                ))
                result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL).returncode
        else:
            with venv(venv_dir) as exe_dir:
                result = run_shell(exe_dir, shell)
    finally:
        result = 1 if result is None else result
        if temp_dir is not None:
            temp_dir.cleanup()

    sys.exit(result)
