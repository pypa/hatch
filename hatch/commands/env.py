import os
import sys

import click

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting
)
from hatch.config import get_venv_dir
from hatch.env import (
    get_editable_packages, get_python_implementation, get_python_version
)
from hatch.settings import load_settings
from hatch.venv import (
    clone_venv, create_venv, fix_available_venvs, get_available_venvs, venv
)


def list_envs(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    venvs = get_available_venvs()

    if venvs:
        echo_success('Virtual environments found in `{}`:\n'.format(get_venv_dir()))
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
                     'one do `hatch env NAME`.'.format(get_venv_dir()))

    ctx.exit()


def restore_envs(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    fix_available_venvs()
    echo_success('Successfully restored all available virtual envs.')
    ctx.exit()


@click.command(context_settings=CONTEXT_SETTINGS,
               short_help='Manages virtual environments')
@click.argument('name')
@click.option('-py', '--python', 'pyname',
              help='The named Python path to use. This overrides --pypath.')
@click.option('-pp', '--pypath',
              help='An absolute path to a Python executable.')
@click.option('-g', '--global-packages', is_flag=True,
              help='Gives the virtual environment access to the global site-packages.')
@click.option('-c', '--clone',
              help='Specifies an existing virtual env to clone. (Experimental)')
@click.option('-v', '--verbose', is_flag=True, help='Increases verbosity.')
@click.option('-r', '--restore', is_flag=True, is_eager=True, callback=restore_envs,
              help=(
                  'Attempts to make all virtual envs in `{}` usable by '
                  'fixing the executable paths in scripts and removing '
                  'all compiled `*.pyc` files. (Experimental)'.format(get_venv_dir())
              ))
@click.option('-l', '--list', 'show', count=True, is_eager=True, callback=list_envs,
              help=(
                  'Shows available virtual envs. Can stack up to 3 times to '
                  'show more info.'
              ))
def env(name, pyname, pypath, global_packages, clone, verbose, restore, show):
    """Creates a new virtual env that can later be utilized with the
    `shell` command.

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

    venv_dir = os.path.join(get_venv_dir(), name)
    if os.path.exists(venv_dir):
        echo_failure('Virtual env `{name}` already exists. To remove '
                     'it do `hatch shed -e {name}`.'.format(name=name))
        sys.exit(1)

    if not clone and not pyname and pypath and not os.path.exists(pypath):
        echo_failure('Python path `{}` does not exist. Be sure to use the absolute path '
                     'e.g. `/usr/bin/python` instead of simply `python`.'.format(pypath))
        sys.exit(1)

    if clone:
        origin = os.path.join(get_venv_dir(), clone)
        if not os.path.exists(origin):
            echo_failure('Virtual env `{name}` does not exist.'.format(name=clone))
            sys.exit(1)
        echo_waiting('Cloning virtual env `{}`...'.format(clone))
        clone_venv(origin, venv_dir)
        echo_success('Successfully cloned virtual env `{}` from `{}` to `{}`.'.format(name, clone, venv_dir))
    else:
        echo_waiting('Creating virtual env `{}`...'.format(name))
        result = create_venv(venv_dir, pypath, use_global=global_packages, verbose=verbose)
        if result == 0:
            echo_success('Successfully saved virtual env `{}` to `{}`.'.format(name, venv_dir))
        else:
            echo_failure('An unexpected failure may have occurred.')
        sys.exit(result)
