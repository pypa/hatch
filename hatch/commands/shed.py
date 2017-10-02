import os
import sys

import click

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_success, echo_warning
)
from hatch.config import get_venv_dir
from hatch.settings import load_settings, save_settings
from hatch.utils import remove_path


@click.command(context_settings=CONTEXT_SETTINGS,
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
            venv_dir = os.path.join(get_venv_dir(), env_name)
            if os.path.exists(venv_dir):
                remove_path(venv_dir)
                echo_success('Successfully removed virtual env named `{}`.'.format(env_name))
            else:
                echo_warning('Virtual env named `{}` already does not exist.'.format(env_name))
