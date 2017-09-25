import os
import sys

import click

from hatch.clean import clean_package, remove_compiled_scripts
from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting
)
from hatch.env import get_editable_package_location
from hatch.utils import resolve_path


@click.command(context_settings=CONTEXT_SETTINGS,
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
@click.option('-nd', '--no-detect', is_flag=True,
              help=(
                  "Disables the detection of a project's dedicated virtual "
                  'env. By default, it will not be considered.'
              ))
@click.option('-v', '--verbose', is_flag=True, help='Shows removed paths.')
def clean(package, local, path, compiled_only, no_detect, verbose):
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
        removed_paths = remove_compiled_scripts(path, detect_project=not no_detect)
    else:
        removed_paths = clean_package(path, editable=package or local, detect_project=not no_detect)

    if verbose:
        if removed_paths:
            echo_success('Removed paths:')
            for p in removed_paths:
                echo_info(p)

    if removed_paths:
        echo_success('Cleaned!')
    else:
        echo_success('Already clean!')
