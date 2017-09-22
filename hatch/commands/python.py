import click

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_success, echo_warning
)


@click.command(context_settings=CONTEXT_SETTINGS,
               short_help='Installs different versions of Python')
def python():  # no cov
    pass
