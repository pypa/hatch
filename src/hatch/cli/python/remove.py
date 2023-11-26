from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Remove Python distributions')
@click.argument('names', required=True, nargs=-1)
@click.option('--dir', '-d', 'directory', help='The directory in which distributions reside')
@click.pass_obj
def remove(app: Application, *, names: tuple[str, ...], directory: str | None):
    """
    Remove Python distributions.

    You may select `all` to remove all installed distributions:

    \b
    ```
    hatch python remove all
    ```
    """
    manager = app.get_python_manager(directory)
    installed = manager.get_installed()
    selection = tuple(installed) if 'all' in names else names
    for name in selection:
        if name not in installed:
            app.display_warning(f'Distribution is not installed: {name}')
            continue

        dist = installed[name]
        with app.status(f'Removing {name}'):
            manager.remove(dist)
