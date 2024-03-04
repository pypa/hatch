from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(
    short_help='Restore the installation', context_settings={'help_option_names': [], 'ignore_unknown_options': True}
)
@click.argument('args', nargs=-1)
@click.pass_obj
def restore(app: Application, *, args: tuple[str, ...]):  # noqa: ARG001
    app.abort('Hatch is not installed as a binary')
