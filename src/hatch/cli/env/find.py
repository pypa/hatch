import click


@click.command(short_help='Locate environments')
@click.argument('env_name', default='default')
@click.pass_obj
def find(app, env_name):
    """Locate environments."""
    app.ensure_environment_plugin_dependencies()

    root_env_name = env_name
    project_config = app.project.config
    if root_env_name not in project_config.envs and root_env_name not in project_config.matrices:
        app.abort(f'Environment `{root_env_name}` is not defined by project config')

    environments = (
        list(project_config.matrices[root_env_name]['envs'])
        if root_env_name in project_config.matrices
        else [root_env_name]
    )

    for env in environments:
        environment = app.get_environment(env)

        try:
            environment.check_compatibility()
        except Exception:  # noqa: BLE001, S112
            continue

        app.display(environment.find())
