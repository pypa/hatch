import click


@click.command(short_help='Create environments')
@click.argument('env_name', default='default')
@click.pass_obj
def create(app, env_name):
    """Create environments."""
    root_env_name = env_name
    project_config = app.project.config
    if root_env_name not in project_config.envs and root_env_name not in project_config.matrices:
        app.abort(f'Environment `{root_env_name}` is not defined by project config')

    if root_env_name in project_config.matrices:
        environments = list(project_config.matrices[root_env_name]['envs'])
    else:
        environments = [root_env_name]

    incompatible = {}
    for env_name in environments:
        environment = app.get_environment(env_name)

        try:
            environment.check_compatibility()
        except Exception as e:
            if root_env_name in project_config.matrices:
                incompatible[env_name] = str(e)
                continue
            else:
                app.abort(f'Environment `{env_name}` is incompatible: {e}')

        if environment.exists():
            app.display_warning(f'Environment `{env_name}` already exists')
            continue

        app.prepare_environment(environment)

    if incompatible:
        num_incompatible = len(incompatible)
        app.display_warning(
            f'Skipped {num_incompatible} incompatible environment{"s" if num_incompatible > 1 else ""}:'
        )
        for env_name, reason in incompatible.items():
            app.display_warning(f'{env_name} -> {reason}')
