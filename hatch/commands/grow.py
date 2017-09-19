import os
import sys

import click

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting,
    echo_warning
)
from hatch.env import get_editable_package_location
from hatch.grow import BUMP, bump_package_version
from hatch.settings import load_settings
from hatch.utils import resolve_path


@click.command(context_settings=CONTEXT_SETTINGS,
               short_help="Increments a project's version")
@click.argument('part', type=click.Choice(BUMP.keys()))
@click.argument('package', required=False)
@click.option('-l', '--local', is_flag=True,
              help=(
                  'Shortcut to select the only available local (editable) '
                  'package. If there are multiple, an error will be raised.'
              ))
@click.option('-p', '--path', help='A relative or absolute path to a project or file.')
@click.option('--pre', 'pre_token',
              help='The token to use for `pre` part, overriding the config file. Default: rc')
@click.option('--build', 'build_token',
              help='The token to use for `build` part, overriding the config file. Default: build')
def grow(part, package, local, path, pre_token, build_token):
    """Increments a project's version number using semantic versioning.
    Valid choices for the part are `major`, `minor`, `patch` (`fix` alias),
    `pre`, and `build`.

    The path to the project is derived in the following order:

    \b
    1. The optional argument, which should be the name of a package
       that was installed via `hatch install -l` or `pip install -e`.
    2. The --local flag.
    3. The option --path, which can be a relative or absolute path.
    4. The current directory.

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
                echo_warning(file)
                echo_failure('\nUnable to find a version specifier.')
            sys.exit(1)
        else:
            echo_failure('No version files found.')
            sys.exit(1)
