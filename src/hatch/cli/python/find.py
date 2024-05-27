from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Locate Python binaries')
@click.argument('name')
@click.option('-p', '--parent', is_flag=True, help='Show the parent directory of the Python binary')
@click.option('--dir', '-d', 'directory', help='The directory in which distributions reside')
@click.pass_obj
def find(app: Application, *, name: str, parent: bool, directory: str | None):
    """Locate Python binaries."""
    manager = app.get_python_manager(directory)
    installed = manager.get_installed()
    if name not in installed:
        app.abort(f'Distribution not installed: {name}')

    dist = installed[name]
    app.display(str(dist.python_path.parent if parent else dist.python_path))
