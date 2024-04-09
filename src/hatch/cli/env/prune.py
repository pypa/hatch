from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Remove all environments')
@click.pass_obj
def prune(app: Application):
    """Remove all environments."""
    app.ensure_environment_plugin_dependencies()

    environment_types = app.plugins.environment.collect()

    for environments in (app.project.config.envs, app.project.config.internal_envs):
        for env_name in environments:
            if env_name == app.env_active:
                app.abort(f'Cannot remove active environment: {env_name}')

        for env_name, config in environments.items():
            environment_type = config['type']
            if environment_type not in environment_types:
                app.abort(f'Environment `{env_name}` has unknown type: {environment_type}')

            environment = environment_types[environment_type](
                app.project.location,
                app.project.metadata,
                env_name,
                config,
                app.project.config.matrix_variables.get(env_name, {}),
                app.get_env_directory(environment_type),
                app.data_dir / 'env' / environment_type,
                app.platform,
                app.verbosity,
            )
            if environment.exists() or environment.build_environment_exists():
                with app.status(f'Removing environment: {env_name}'):
                    environment.remove()
