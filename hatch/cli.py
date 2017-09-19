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
from hatch.commands import (
    conda, config, init, install, new, python, uninstall
)
from hatch.commands.utils import (
    CONTEXT_SETTINGS, UNKNOWN_OPTIONS, echo_failure, echo_info, echo_success,
    echo_warning, echo_waiting
)
from hatch.env import (
    get_editable_packages, get_editable_package_location, get_installed_packages,
    get_python_version, get_python_implementation, install_packages
)
from hatch.grow import BUMP, bump_package_version
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, load_settings, save_settings
)
from hatch.shells import run_shell
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, ON_WINDOWS, basepath, chdir, get_admin_command,
    get_proper_pip, get_proper_python, get_random_venv_name, get_requirements_file,
    remove_path, resolve_path, venv_active
)
from hatch.venv import (
    VENV_DIR, clone_venv, create_venv, fix_available_venvs, get_available_venvs,
    is_venv, venv
)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def hatch():
    pass


hatch.add_command(conda)
hatch.add_command(config)
hatch.add_command(init)
hatch.add_command(install)
hatch.add_command(new)
hatch.add_command(python)
hatch.add_command(uninstall)


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Updates packages')
@click.argument('packages', nargs=-1)
@click.option('-nd', '--no-detect', is_flag=True,
              help=(
                  "Disables the use of a project's dedicated virtual env. "
                  'This is useful if you need to be in a project root but '
                  'wish to not target its virtual env.'
              ))
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
@click.option('--admin', is_flag=True,
              help=(
                  'When --global is selected, this assumes admin rights are '
                  'already enabled and therefore sudo/runas will not be used.'
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
def update(packages, no_detect, env_name, eager, all_packages, infra, global_install,
           admin, force, dev, as_module, self, quiet):
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

    If no --env is chosen, this will attempt to detect a project and use its
    virtual env before resorting to the default pip.

    To update this tool, use the --self flag. All other methods of updating will
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

    if not self and env_name:
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
    elif not self and not no_detect and os.path.isfile(os.path.join(os.getcwd(), 'setup.py')):
        venv_dir = os.path.join(os.getcwd(), 'venv')
        if not is_venv(venv_dir):
            echo_info('A project has been detected!')
            echo_waiting('Creating a dedicated virtual env... ', nl=False)
            create_venv(venv_dir)
            echo_success('complete!')

            with venv(venv_dir):
                echo_waiting('Installing this project in the virtual env... ', nl=False)
                install_packages(['-q', '-e', '.'])
                echo_success('complete!')

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
                if not admin:
                    if ON_WINDOWS:
                        windows_admin_command = get_admin_command()
                    else:
                        command = get_admin_command() + command
            else:
                command.append('--user')

    if self:  # no cov
        command.append('hatch')
        if ON_WINDOWS:
            echo_warning('After the update you may want to press Enter to flush stdout.')
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
            if env_name:
                echo_waiting('Updating virtual env `{}`...'.format(env_name))
            else:
                echo_waiting('Updating for this project...')
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    else:
        echo_waiting('Updating...')
        result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)

    if temp_dir is not None:
        temp_dir.cleanup()

    sys.exit(result.returncode)


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Runs tests')
@click.argument('package', required=False)
@click.option('-l', '--local', is_flag=True,
              help=(
                  'Shortcut to select the only available local (editable) '
                  'package. If there are multiple, an error will be raised.'
              ))
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
@click.option('-g', '--global', 'global_exe', is_flag=True,
              help=(
                  'Uses the `pytest` and `coverage` shipped with Hatch instead '
                  'of environment-aware modules. This is useful if you just want '
                  'want to run a quick test without installing these again in a '
                  'virtual env. Keep in mind these will be the Python 3 versions.'
              ))
def test(package, local, path, cov, merge, test_args, cov_args, global_exe):
    """Runs tests using `pytest`, optionally checking coverage.

    The path is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `hatch install -l` or `pip install -e`.
    2. The --local flag.
    3. The option --path, which can be a relative or absolute path.
    4. The current directory.

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
        echo_waiting('Locating package...')
        path = get_editable_package_location(package)
        if not path:
            echo_failure('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif local:
        echo_waiting('Locating package...')
        name, path = get_editable_package_location()
        if not name:
            if path is None:
                echo_failure('There are no local packages available.')
                sys.exit(1)
            else:
                echo_failure(
                    'There are multiple local packages available. Select '
                    'one with the optional argument.'
                )
                sys.exit(1)
        echo_info('Package `{}` has been selected.'.format(name))
    elif path:
        possible_path = resolve_path(path)
        if not possible_path:
            echo_failure('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
        path = possible_path
    else:
        path = os.getcwd()

    python_cmd = [sys.executable if global_exe else get_proper_python(), '-m']
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
            echo_waiting('\nTests completed, checking coverage...\n')

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

    sys.exit(test_result.returncode)


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help="Removes a project's build artifacts")
@click.argument('package', required=False)
@click.option('-l', '--local', is_flag=True,
              help=(
                  'Shortcut to select the only available local (editable) '
                  'package. If there are multiple, an error will be raised.'
              ))
@click.option('-p', '--path', help='A relative or absolute path to a project.')
@click.option('-c', '--compiled-only', is_flag=True,
              help='Removes only .pyc files.')
@click.option('-v', '--verbose', is_flag=True, help='Shows removed paths.')
def clean(package, local, path, compiled_only, verbose):
    """Removes a project's build artifacts.

    The path to the project is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `hatch install -l` or `pip install -e`.
    2. The --local flag.
    3. The option --path, which can be a relative or absolute path.
    4. The current directory.

    All `*.pyc`/`*.pyd`/`*.pyo` files and `__pycache__` directories will be removed.
    Additionally, the following patterns will be removed from the root of the path:
    `.cache`, `.coverage`, `.eggs`, `.tox`, `build`, `dist`, and `*.egg-info`.

    If the path was derived from the optional package argument, the pattern
    `*.egg-info` will not be applied so as to not break that installation.
    """
    if package:
        echo_waiting('Locating package...')
        path = get_editable_package_location(package)
        if not path:
            echo_failure('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif local:
        echo_waiting('Locating package...')
        name, path = get_editable_package_location()
        if not name:
            if path is None:
                echo_failure('There are no local packages available.')
                sys.exit(1)
            else:
                echo_failure(
                    'There are multiple local packages available. Select '
                    'one with the optional argument.'
                )
                sys.exit(1)
        echo_info('Package `{}` has been selected.'.format(name))
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
        removed_paths = clean_package(path, editable=package or local)

    if verbose:
        if removed_paths:
            echo_success('Removed paths:')
            for p in removed_paths:
                echo_info(p)

    if removed_paths:
        echo_success('Cleaned!')
    else:
        echo_success('Already clean!')


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Builds a project')
@click.argument('package', required=False)
@click.option('-l', '--local', is_flag=True,
              help=(
                  'Shortcut to select the only available local (editable) '
                  'package. If there are multiple, an error will be raised.'
              ))
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
def build(package, local, path, pyname, pypath, universal, name, build_dir,
          clean_first, verbose):
    """Builds a project, producing a source distribution and a wheel.

    The path to the project is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `hatch install -l` or `pip install -e`.
    2. The --local flag.
    3. The option --path, which can be a relative or absolute path.
    4. The current directory.

    The path must contain a `setup.py` file.
    """
    if package:
        echo_waiting('Locating package...')
        path = get_editable_package_location(package)
        if not path:
            echo_failure('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif local:
        echo_waiting('Locating package...')
        name, path = get_editable_package_location()
        if not name:
            if path is None:
                echo_failure('There are no local packages available.')
                sys.exit(1)
            else:
                echo_failure(
                    'There are multiple local packages available. Select '
                    'one with the optional argument.'
                )
                sys.exit(1)
        echo_info('Package `{}` has been selected.'.format(name))
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
        echo_waiting('Removing build artifacts...')
        clean_package(path, editable=package or local)

    return_code = build_package(path, build_dir, universal, name, pypath, verbose)

    if os.path.isdir(build_dir):
        echo_success('Files found in `{}`:\n'.format(build_dir))
        for file in sorted(os.listdir(build_dir)):
            if os.path.isfile(os.path.join(build_dir, file)):
                echo_info(file)

    sys.exit(return_code)


@hatch.command(context_settings=CONTEXT_SETTINGS, short_help='Uploads to PyPI')
@click.argument('package', required=False)
@click.option('-l', '--local', is_flag=True,
              help=(
                  'Shortcut to select the only available local (editable) '
                  'package. If there are multiple, an error will be raised.'
              ))
@click.option('-p', '--path',
              help='A relative or absolute path to a build directory.')
@click.option('-u', '--username', help='The PyPI username to use.')
@click.option('-t', '--test', 'test_pypi', is_flag=True,
              help='Uses the test version of PyPI.')
@click.option('-s', '--strict', is_flag=True,
              help='Aborts if a distribution already exists.')
def release(package, local, path, username, test_pypi, strict):
    """Uploads all files in a directory to PyPI using Twine.

    The path to the build directory is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `hatch install -l` or `pip install -e`.
    2. The --local flag.
    3. The option --path, which can be a relative or absolute path.
    4. The current directory. If the current directory has a `dist`
       directory, that will be used instead.

    If the path was derived from the optional package argument, the
    files must be in a directory named `dist`.

    The PyPI username can be saved in the config file entry `pypi_username`.
    If the `TWINE_PASSWORD` environment variable is not set, a hidden prompt
    will be provided for the password.
    """
    if package:
        echo_waiting('Locating package...')
        path = get_editable_package_location(package)
        if not path:
            echo_failure('`{}` is not an editable package.'.format(package))
            sys.exit(1)
        path = os.path.join(path, 'dist')
    elif local:
        echo_waiting('Locating package...')
        name, path = get_editable_package_location()
        if not name:
            if path is None:
                echo_failure('There are no local packages available.')
                sys.exit(1)
            else:
                echo_failure(
                    'There are multiple local packages available. Select '
                    'one with the optional argument.'
                )
                sys.exit(1)
        echo_info('Package `{}` has been selected.'.format(name))
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
            echo_success('{} -> '.format(p), nl=False)
            echo_info('{}'.format(pypaths[p]))
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
                    echo_info('  Version: {}'.format(get_python_version()))
                elif value == 2:
                    echo_info('  Version: {}'.format(get_python_version()))
                    echo_info('  Implementation: {}'.format(get_python_implementation()))
                else:
                    echo_info('  Version: {}'.format(get_python_version()))
                    echo_info('  Implementation: {}'.format(get_python_implementation()))
                    echo_info('  Local packages: {}'.format(', '.join(sorted(get_editable_packages()))))

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
@click.option('-s', '--shell',
              help=(
                  'The name of shell to use e.g. `bash`. If the shell name '
                  'is not supported, e.g. `bash -O`, it will be treated as '
                  'a command and no custom prompt will be provided. This '
                  'overrides the config file entry `shell`.'
              ))
@click.option('-t', '--temp', 'temp_env', is_flag=True,
              help='Use a new temporary virtual env.')
@click.option('-py', '--python', 'pyname',
              help=(
                  'A named Python path to use when creating a temporary '
                  'virtual env. This overrides --pypath.'
              ))
@click.option('-pp', '--pypath',
              help=(
                  'An absolute path to a Python executable to use when '
                  'creating a temporary virtual env.'
              ))
def use(env_name, command, shell, temp_env, pyname, pypath):  # no cov
    """Activates or sends a command to a virtual environment. A default shell
    name (or command) can be specified in the config file entry `shell` or the
    environment variable `SHELL`. If there is no entry, env var, nor shell
    option provided, a system default will be used: `cmd` on Windows, `bash`
    otherwise.

    Any arguments provided after the first will be sent to the virtual env as
    a command without activating it. If there is only the env without args,
    it will be activated similarly to how you are accustomed. The name of
    the virtual env to use must be omitted if using the --temp env option.
    If no env is chosen, this will attempt to detect a project and activate
    its virtual env. To run a command in a project's virtual env, use `.` as
    the env name.

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
    venv_dir = None
    if resolve_path(env_name) == os.getcwd():
        env_name = ''

    if not (env_name or temp_env):
        if os.path.isfile(os.path.join(os.getcwd(), 'setup.py')):
            venv_dir = os.path.join(os.getcwd(), 'venv')
            if not is_venv(venv_dir):
                echo_info('A project has been detected!')
                echo_waiting('Creating a dedicated virtual env... ', nl=False)
                create_venv(venv_dir)
                echo_success('complete!')

                with venv(venv_dir):
                    echo_waiting('Installing this project in the virtual env... ', nl=False)
                    install_packages(['-q', '-e', '.'])
                    echo_success('complete!')
        else:
            echo_failure('No project found.')
            sys.exit(1)

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

        temp_dir = TemporaryDirectory()
        env_name = get_random_venv_name()
        venv_dir = os.path.join(temp_dir.name, env_name)
        echo_waiting('Creating a temporary virtual env named `{}`...'.format(env_name))
        create_venv(venv_dir, pypath=pypath, verbose=True)
    else:
        temp_dir = None
        venv_dir = venv_dir or os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            echo_failure('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

    result = None

    try:
        if command:
            with venv(venv_dir):
                echo_waiting('Running `{}` in {}...'.format(
                    ' '.join(c if len(c.split()) == 1 else '"{}"'.format(c) for c in command),
                    '`{}`'.format(env_name) if env_name else "this project's env"
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
