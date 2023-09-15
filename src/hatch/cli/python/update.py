from __future__ import annotations

from typing import TYPE_CHECKING

import click

from hatch.cli.python.install import install

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Update Python distributions')
@click.argument('names', required=True, nargs=-1)
@click.option('--dir', '-d', 'directory', help='The directory in which distributions reside')
@click.pass_context
def update(ctx: click.Context, *, names: tuple[str, ...], directory: str | None):
    """
    Update Python distributions.

    You may select `all` to update all installed distributions:

    \b
    ```
    hatch python update all
    ```
    """
    app: Application = ctx.obj

    manager = app.get_python_manager(directory)
    installed = manager.get_installed()
    selection = tuple(installed) if 'all' in names else names

    not_installed = [name for name in selection if name not in installed]
    if not_installed:
        app.abort(f'Distributions not installed: {", ".join(not_installed)}')

    ctx.invoke(install, names=selection, directory=directory, private=True, update=True)
