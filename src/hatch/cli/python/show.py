from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Show the available Python distributions')
@click.option('--ascii', 'force_ascii', is_flag=True, help='Whether or not to only use ASCII characters')
@click.option('--dir', '-d', 'directory', help='The directory in which distributions reside')
@click.pass_obj
def show(app: Application, *, force_ascii: bool, directory: str | None):
    """Show the available Python distributions."""
    from hatch.python.resolve import get_compatible_distributions

    manager = app.get_python_manager(directory)
    installed = manager.get_installed()

    installed_columns: dict[str, dict[int, str]] = {'Name': {}, 'Version': {}, 'Status': {}}
    for i, (name, installed_dist) in enumerate(installed.items()):
        installed_columns['Name'][i] = name
        installed_columns['Version'][i] = installed_dist.version
        if installed_dist.needs_update():
            installed_columns['Status'][i] = 'Update available'

    available_columns: dict[str, dict[int, str]] = {'Name': {}, 'Version': {}}
    for i, (name, dist) in enumerate(get_compatible_distributions().items()):
        if name in installed:
            continue

        available_columns['Name'][i] = name
        available_columns['Version'][i] = dist.version.base_version

    app.display_table('Installed', installed_columns, show_lines=True, force_ascii=force_ascii)
    app.display_table('Available', available_columns, show_lines=True, force_ascii=force_ascii)
