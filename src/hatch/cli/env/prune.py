import click


@click.command(short_help='Remove all environments')
@click.pass_obj
def prune(app):
    """Remove all environments."""
    environment_types = app.plugins.environment.collect()

    environments = app.project.config.envs
    for env_name in environments:
        if env_name == app.env_active:
            app.abort(f'Cannot remove active environment: {env_name}')

    for env_name, config in environments.items():
        environment_type = config['type']
        if environment_type not in environment_types:
            app.abort(f'Environment `{env_name}` has unknown type: {environment_type}')

        data_dir = app.get_env_directory(environment_type)

        environment = environment_types[environment_type](
            app.project.location,
            app.project.metadata,
            env_name,
            config,
            app.project.config.matrix_variables.get(env_name, {}),
            data_dir,
            app.platform,
            app.verbosity,
        )

        try:
            environment.check_compatibility()
        except Exception:
            continue

        if environment.exists() or environment.build_environment_exists():
            with app.status_waiting(f'Removing environment: {env_name}'):
                environment.remove()
