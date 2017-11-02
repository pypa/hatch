import os
import sys

import click

from hatch.build import build_package
from hatch.clean import clean_package
from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting
)
from hatch.env import get_editable_package_location
from hatch.settings import load_settings
from hatch.utils import basepath, resolve_path


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Builds a project')
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
        clean_package(path, editable=package or local, detect_project=True)

    # basic handling of https://github.com/pypa/setuptools/issues/1185
    bd = basepath(build_dir) if build_dir == os.path.join(path, 'dist') else build_dir

    return_code = build_package(path, bd, universal, name, pypath, verbose)

    if os.path.isdir(build_dir):
        echo_success('Files found in `{}`:\n'.format(build_dir))
        for file in sorted(os.listdir(build_dir)):
            if os.path.isfile(os.path.join(build_dir, file)):
                echo_info(file)

    sys.exit(return_code)
