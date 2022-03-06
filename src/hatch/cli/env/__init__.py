import click


@click.group(short_help='Manage project environments')
def env():
    pass


@env.command(short_help='Locate environments')
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

        app.display_info(environment.find())


@env.command(short_help='Show the available environments')
@click.option('--ascii', 'force_ascii', is_flag=True, help='Whether or not to only use ASCII characters')
@click.pass_obj
def show(app, force_ascii):
    """Show the available environments."""
    from ...utils.dep import get_normalized_dependencies

    project_config = app.project.config

    def set_available_columns(columns):
        if config.get('dependencies'):
            columns['Dependencies'][i] = '\n'.join(get_normalized_dependencies(config['dependencies']))

        if config.get('env-vars'):
            columns['Environment variables'][i] = '\n'.join(
                sorted('='.join(item) for item in config['env-vars'].items())
            )

        if config.get('description'):
            columns['Description'][i] = config['description'].strip()

    matrix_columns = {
        'Name': {},
        'Type': {},
        'Envs': {},
        'Dependencies': {},
        'Environment variables': {},
        'Description': {},
    }
    matrix_envs = set()
    for i, (matrix_name, matrix_data) in enumerate(project_config.matrices.items()):
        for env_name in matrix_data['envs']:
            matrix_envs.add(env_name)

        config = matrix_data['config']
        matrix_columns['Name'][i] = matrix_name
        matrix_columns['Type'][i] = config['type']
        matrix_columns['Envs'][i] = '\n'.join(matrix_data['envs'])
        set_available_columns(matrix_columns)

    standalone_columns = {'Name': {}, 'Type': {}, 'Dependencies': {}, 'Environment variables': {}, 'Description': {}}
    standalone_envs = (
        (env_name, config) for env_name, config in project_config.envs.items() if env_name not in matrix_envs
    )
    for i, (env_name, config) in enumerate(standalone_envs):
        standalone_columns['Name'][i] = env_name
        standalone_columns['Type'][i] = config['type']
        set_available_columns(standalone_columns)

    column_options = {}
    for title in matrix_columns:
        if title != 'Description':
            column_options[title] = {'no_wrap': True}

    app.display_table(
        'Standalone', standalone_columns, show_lines=True, column_options=column_options, force_ascii=force_ascii
    )
    app.display_table(
        'Matrices', matrix_columns, show_lines=True, column_options=column_options, force_ascii=force_ascii
    )


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


@env.command(short_help='Remove environments')
@click.argument('env_name', default='default')
@click.pass_context
def remove(ctx, env_name):
    """Remove environments."""
    app = ctx.obj
    if ctx.get_parameter_source('env_name').name == 'DEFAULT':
        env_name = app.env

    if env_name in app.project.config.matrices:
        environments = list(app.project.config.matrices[env_name]['envs'])
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
