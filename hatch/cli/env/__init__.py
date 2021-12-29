import click


@click.group(short_help='Manage project environments')
def env():
    pass


@env.command(short_help='Show the available environments')
@click.pass_obj
def show(app):
    """Show the available environments."""
    project_config = app.project.config

    matrix_envs = set()
    for env_names in project_config.matrices.values():
        for env_name in env_names:
            matrix_envs.add(env_name)

    need_new_line = False
    for env_name in project_config.envs:
        if env_name not in matrix_envs:
            need_new_line = True
            app.display_info(env_name)

    for matrix, env_names in project_config.matrices.items():
        if need_new_line:
            app.display_info()

        if matrix == 'default':
            for env_name in env_names:
                app.display_info(env_name)
        else:
            app.display_mini_header(matrix)

            prefix_length = len(matrix) + 1
            for env_name in env_names:
                app.display_info(env_name[prefix_length:])

        need_new_line = True


@env.command(short_help='Create environments')
@click.argument('env_name', default='default')
@click.pass_obj
def create(app, env_name):
    """Create environments."""
    root_env_name = env_name
    project_config = app.project.config
    if root_env_name not in project_config.envs and root_env_name not in project_config.matrices:
        app.abort(f'Environment `{root_env_name}` is not defined by project config')

    if root_env_name in project_config.matrices:
        environments = project_config.matrices[root_env_name]
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


@env.command(short_help='Remove environments')
@click.argument('env_name', default='default')
@click.pass_context
def remove(ctx, env_name):
    """Remove environments."""
    app = ctx.obj
    if ctx.get_parameter_source('env_name').name == 'DEFAULT':
        env_name = app.env

    if env_name in app.project.config.matrices:
        environments = app.project.config.matrices[env_name]
    else:
        environments = [env_name]

    for env_name in environments:
        if env_name == app.env_active:
            app.abort(f'Cannot remove active environment: {env_name}')

    for env_name in environments:
        environment = app.get_environment(env_name)

        try:
            environment.check_compatibility()
        except Exception:
            continue

        if environment.exists():
            environment.remove()


@env.command(short_help='Remove all environments')
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
            app.abort(f'Environment `{app.env}` has unknown type: {environment_type}')

        data_dir = app.get_env_directory(environment_type)

        environment = environment_types[environment_type](
            app.project.location, app.project.metadata, env_name, config, data_dir, app.platform, app.verbosity
        )

        try:
            environment.check_compatibility()
        except Exception:
            continue

        if environment.exists():
            environment.remove()
