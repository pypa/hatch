import sys

import click

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success
)
from hatch.settings import copy_default_settings, load_settings, save_settings


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


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Manages named Python paths')
@click.argument('name')
@click.argument('path')
@click.option('-l', '--list', 'show', is_flag=True, is_eager=True, callback=list_pypaths,
              help='Shows available Python paths.')
def pypath(name, path, show):
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
