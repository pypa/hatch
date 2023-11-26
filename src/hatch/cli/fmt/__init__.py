from __future__ import annotations

from typing import TYPE_CHECKING, cast

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Lint and format source code')
@click.argument('args', nargs=-1)
@click.option('--check', is_flag=True, help='Only check for errors rather than fixing them')
@click.option('--preview/--no-preview', default=None, help='Preview new rules and formatting')
@click.option('--linter', '-l', is_flag=True, help='Only run the linter')
@click.option('--formatter', '-f', is_flag=True, help='Only run the formatter')
@click.option('--sync', is_flag=True, help='Sync the default config file with the current version of Hatch')
@click.pass_obj
def fmt(
    app: Application,
    *,
    args: tuple[str, ...],
    check: bool,
    preview: bool | None,
    linter: bool,
    formatter: bool,
    sync: bool,
):
    """Format and lint source code."""
    from hatch.env.internal.fmt import InternalFormatEnvironment

    if linter and formatter:
        app.abort('Cannot specify both --linter and --formatter')

    environment = cast(
        InternalFormatEnvironment, app.prepare_internal_environment('fmt', config=app.project.config.fmt)
    )
    if sync and not environment.config_path:
        app.abort('The --sync flag can only be used when the `tool.hatch.format.config-path` option is defined')

    commands: list[list[str]] = []
    if not formatter:
        commands.append(environment.get_linter_command(*args, check=check, preview=preview))

    if not linter:
        commands.append(environment.get_formatter_command(*args, check=check, preview=preview))

    with app.project.location.as_cwd(), environment.command_context():
        if not environment.config_path or sync:
            environment.write_config_file(preview=preview)

        for command in commands:
            process = app.platform.run_command(command)
            if process.returncode:
                app.abort(code=process.returncode)
