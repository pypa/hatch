from __future__ import annotations

from typing import TYPE_CHECKING

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
    from hatch.cli.fmt.core import FormatEnvironment

    if linter and formatter:
        app.abort('Cannot specify both --linter and --formatter')

    internal_env = app.get_environment('hatch-static-analysis')
    if not internal_env.exists():
        try:
            internal_env.check_compatibility()
        except Exception as e:  # noqa: BLE001
            app.abort(f'Environment is incompatible: {e}')

    app.prepare_environment(internal_env)
    environment = FormatEnvironment(internal_env)

    # TODO: remove in a few minor releases, this is very new but we don't want to break users on the cutting edge
    if legacy_config_path := app.project.config.config.get('format', {}).get('config-path', ''):
        app.display_warning(
            'The `tool.hatch.format.config-path` option is deprecated and will be removed in a future release. '
            'Use `tool.hatch.envs.hatch-static-analysis.config-path` instead.'
        )
        environment.config_path = legacy_config_path

    if sync and not environment.config_path:
        app.abort('The --sync flag can only be used when the `tool.hatch.format.config-path` option is defined')

    commands: list[list[str]] = []
    if not formatter:
        commands.append(environment.get_linter_command(*args, check=check, preview=preview))

    if not linter:
        commands.append(environment.get_formatter_command(*args, check=check, preview=preview))

    with app.project.location.as_cwd(), internal_env.command_context():
        if not environment.config_path or sync:
            environment.write_config_file(preview=preview)

        for command in commands:
            process = app.platform.run_command(command)
            if process.returncode:
                app.abort(code=process.returncode)
