import click


@click.command(short_help='Upgrade environment dependencies')
@click.argument('env_name', default='default')
@click.argument('strategy', default='only-if-needed')
@click.pass_context
def upgrade(ctx, env_name, strategy) -> None:
    app = ctx.obj

    if ctx.get_parameter_source('env_name').name == 'DEFAULT':
        env_name = app.env

    environments = (
        list(app.project.config.matrices[env_name]['envs']) if env_name in app.project.config.matrices else [env_name]
    )

    for env_name in environments:
        environment = app.get_environment(env_name)

        try:
            environment.check_compatibility()
        except Exception:  # noqa: S112
            continue

        if environment.exists() or environment.build_environment_exists():
            with app.status_waiting(f'Upgrading environment: {env_name}'):
                environment.upgrade_dependencies(strategy)
