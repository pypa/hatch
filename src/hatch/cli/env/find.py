import click


@click.command(short_help='Locate environments')
@click.argument('env_name', default='default')
@click.pass_obj
def find(app, env_name):
    """Locate environments."""
    root_env_name = env_name
    project_config = app.project.config
    if root_env_name not in project_config.envs and root_env_name not in project_config.matrices:
        app.abort(f'Environment `{root_env_name}` is not defined by project config')

    if root_env_name in project_config.matrices:
        environments = list(project_config.matrices[root_env_name]['envs'])
    else:
        environments = [root_env_name]

    for env_name in environments:
        environment = app.get_environment(env_name)

        try:
            environment.check_compatibility()
        except Exception:
            continue

        app.display_always(environment.find())
