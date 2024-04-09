from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Create environments')
@click.argument('env_name', default='default')
@click.pass_obj
def create(app: Application, env_name: str):
    """Create environments."""
    app.ensure_environment_plugin_dependencies()

    environments = app.expand_environments(env_name)
    if not environments:
        app.abort(f'Environment `{env_name}` is not defined by project config')

    incompatible = {}
    for env in environments:
        environment = app.get_environment(env)
        if environment.exists():
            app.display_warning(f'Environment `{env}` already exists')
            continue

        try:
            environment.check_compatibility()
        except Exception as e:  # noqa: BLE001
            if env_name in app.project.config.matrices:
                incompatible[env] = str(e)
                continue

            app.abort(f'Environment `{env}` is incompatible: {e}')

        app.prepare_environment(environment)

    if incompatible:
        num_incompatible = len(incompatible)
        app.display_warning(
            f'Skipped {num_incompatible} incompatible environment{"s" if num_incompatible > 1 else ""}:'
        )
        for env, reason in incompatible.items():
            app.display_warning(f'{env} -> {reason}')
