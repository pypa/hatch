import click


@click.command(short_help='Remove environments')
@click.argument('env_name', default='default')
@click.pass_context
def remove(ctx, env_name):
    """Remove environments."""
    app = ctx.obj
    app.ensure_environment_plugin_dependencies()

    if ctx.get_parameter_source('env_name').name == 'DEFAULT':
        env_name = app.env

    environments = (
        list(app.project.config.matrices[env_name]['envs']) if env_name in app.project.config.matrices else [env_name]
    )

    for env_name in environments:
        if env_name == app.env_active:
            app.abort(f'Cannot remove active environment: {env_name}')

    for env_name in environments:
        environment = app.get_environment(env_name)

        try:
            environment.check_compatibility()
        except Exception:  # noqa: BLE001, S112
            continue

        if environment.exists() or environment.build_environment_exists():
            with app.status(f'Removing environment: {env_name}'):
                environment.remove()
