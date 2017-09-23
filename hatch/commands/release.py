import os
import subprocess
import sys

import click
from twine.utils import DEFAULT_REPOSITORY, TEST_REPOSITORY

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_waiting
)
from hatch.env import get_editable_package_location
from hatch.settings import SETTINGS_FILE, load_settings
from hatch.utils import NEED_SUBPROCESS_SHELL, resolve_path


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Uploads to PyPI')
@click.argument('package', required=False)
@click.option('-l', '--local', is_flag=True,
              help=(
                  'Shortcut to select the only available local (editable) '
                  'package. If there are multiple, an error will be raised.'
              ))
@click.option('-p', '--path',
              help='A relative or absolute path to a build directory.')
@click.option('-u', '--username', help='The PyPI username to use.')
@click.option('-r', '--repo',
              help=(
                  'The PyPI repository to use (default: {}). '
                  'Should be a section in the .pypirc file. '
                  '(Can also be set via TWINE_REPOSITORY environment variable)'
              ).format(DEFAULT_REPOSITORY))
@click.option('-ru', '--repo-url',
              help=(
                  'The repository URL to upload the package to. '
                  'This overrides --repository. '
                  '(Can also be set via TWINE_REPOSITORY_URL environment variable)'
              ))
@click.option('-t', '--test', 'test_pypi', is_flag=True,
              help='Uses the test version of PyPI. Equivalent to \'-r {}\''.format(TEST_REPOSITORY))
@click.option('-s', '--strict', is_flag=True,
              help='Aborts if a distribution already exists.')
def release(package, local, path, username, repo, repo_url, test_pypi, strict):
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

    The PyPI username can be saved in the config file entry `pypi_username`
    or the `TWINE_USERNAME` environment variable.
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

        # Fall back when 'pypi_username' value is '' or None
        username = settings.get('pypi_username') or os.environ.get('TWINE_USERNAME')
        if not username:
            echo_failure(
                'A username must be supplied via -u/--username, '
                'in {} as pypi_username, or in the TWINE_USERNAME '
                'environment variable.'.format(SETTINGS_FILE)
            )
            sys.exit(1)

    command = [sys.executable, '-m', 'twine', 'upload', '-u', username,
               '{}{}*'.format(path, os.path.sep)]

    if test_pypi:
        # Print all error messages before exiting
        any_failed = False
        # Disallow these combinations, since it is ambiguous whether they are intended
        # to be used as the test repository (if a custom test repository is desired,
        # then users can omit the '--test'.)
        if repo:
            echo_failure('Cannot specify both --test and --repo.')
            any_failed = True
        if repo_url:
            echo_failure('Cannot specify both --test and --repo-url.')
            any_failed = True
        if any_failed:
            sys.exit(1)
        command.extend(['-r', TEST_REPOSITORY, '--repository-url', TEST_REPOSITORY])
    else:  # no cov
        # Only pass these to twine if they are given to us. Otherwise,
        # fall back onto the default twine behavior
        if repo:
            command.extend(['-r', repo])
        if repo_url:
            command.extend(['--repository-url', repo_url])

    if not strict:
        command.append('--skip-existing')

    result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    sys.exit(result.returncode)
