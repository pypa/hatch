import io
import os
import subprocess
import sys

import click

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting
)
from hatch.config import get_proper_python
from hatch.env import get_editable_package_location, install_packages
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, chdir, get_requirements_file, is_project,
    resolve_path, venv_active
)
from hatch.venv import create_venv, is_venv, venv


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Runs tests')
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
                  'Uses the `pytest` and `coverage` shipped with Hatch instead of '
                  'environment-aware modules. This is useful if you just want to '
                  'run a quick test without installing these again in a virtual '
                  'env. Keep in mind these will be the Python 3 versions.'
              ))
@click.option('-nd', '--no-detect', is_flag=True,
              help=(
                  "Does not run the tests inside a project's dedicated virtual env."
              ))
def test(package, local, path, cov, merge, test_args, cov_args, global_exe, no_detect):
    """Runs tests using `pytest`, optionally checking coverage.

    The path is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `hatch install -l` or `pip install -e`.
    2. The --local flag.
    3. The option --path, which can be a relative or absolute path.
    4. The current directory.

    If the path points to a package, it should have a `tests` directory.

    If a project is detected but there is no dedicated virtual env, it
    will be created and any dev requirements will be installed in it.

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

    venv_dir = None
    if not (package or local) and not venv_active() and not no_detect and is_project():
        venv_dir = os.path.join(path, 'venv')
        if not is_venv(venv_dir):
            echo_info('A project has been detected!')
            echo_waiting('Creating a dedicated virtual env... ', nl=False)
            create_venv(venv_dir)
            echo_success('complete!')

            with venv(venv_dir):
                echo_waiting('Installing this project in the virtual env...')
                install_packages(['-e', '.'])
                click.echo()

                echo_waiting('Ensuring pytest and coverage are available...')
                install_packages(['pytest', 'coverage'])
                click.echo()

                dev_requirements = get_requirements_file(path, dev=True)
                if dev_requirements:
                    echo_waiting('Installing test dependencies in the virtual env...')
                    install_packages(['-r', dev_requirements])
                    click.echo()

    with chdir(path):
        echo_waiting('Testing...')
        output = b''

        if venv_dir:
            with venv(venv_dir):
                test_result = subprocess.run(
                    command,
                    stdout=stdout, stderr=stderr,
                    shell=NEED_SUBPROCESS_SHELL
                )
        else:
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
                if venv_dir:
                    with venv(venv_dir):
                        result = subprocess.run(
                            python_cmd + ['coverage', 'combine', '--append'],
                            stdout=stdout, stderr=stderr,
                            shell=NEED_SUBPROCESS_SHELL
                        )
                else:
                    result = subprocess.run(
                        python_cmd + ['coverage', 'combine', '--append'],
                        stdout=stdout, stderr=stderr,
                        shell=NEED_SUBPROCESS_SHELL
                    )
                output += result.stdout or b''
                output += result.stderr or b''

            if venv_dir:
                with venv(venv_dir):
                    result = subprocess.run(
                        python_cmd + ['coverage', 'report', '--show-missing'],
                        stdout=stdout, stderr=stderr,
                        shell=NEED_SUBPROCESS_SHELL
                    )
            else:
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
