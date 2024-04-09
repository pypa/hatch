from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Locate environments')
@click.argument('env_name', default='default')
@click.pass_obj
def find(app: Application, env_name: str):
    """Locate environments."""
    app.ensure_environment_plugin_dependencies()

    environments = app.expand_environments(env_name)
    if not environments:
        app.abort(f'Environment `{env_name}` is not defined by project config')

    for env in environments:
        environment = app.get_environment(env)
        app.display(environment.find())
