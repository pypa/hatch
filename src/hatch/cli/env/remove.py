from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Remove environments')
@click.argument('env_name', default='default')
@click.pass_context
def remove(ctx: click.Context, env_name: str):
    """Remove environments."""
    app: Application = ctx.obj
    app.ensure_environment_plugin_dependencies()

    if (parameter_source := ctx.get_parameter_source('env_name')) is not None and parameter_source.name == 'DEFAULT':
        env_name = app.env

    environments = app.expand_environments(env_name)
    if not environments:
        app.abort(f'Environment `{env_name}` is not defined by project config')

    for env_name in environments:
        if env_name == app.env_active:
            app.abort(f'Cannot remove active environment: {env_name}')

    for env_name in environments:
        environment = app.get_environment(env_name)
        if environment.exists() or environment.build_environment_exists():
            with app.status(f'Removing environment: {env_name}'):
                environment.remove()
