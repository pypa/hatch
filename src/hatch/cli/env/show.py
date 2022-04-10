import click


@click.command(short_help='Show the available environments')
@click.argument('envs', required=False, nargs=-1)
@click.option('--ascii', 'force_ascii', is_flag=True, help='Whether or not to only use ASCII characters')
@click.option('--json', 'as_json', is_flag=True, help='Whether or not to output in JSON format')
@click.pass_obj
def show(app, envs, force_ascii, as_json):
    """Show the available environments."""
    if as_json:
        import json

        app.display_info(json.dumps(app.project.config.envs))
        return

    from hatchling.metadata.utils import normalize_project_name

    from ...utils.dep import get_normalized_dependencies

    project_config = app.project.config

    def set_available_columns(columns):
        if config.get('features'):
            columns['Features'][i] = '\n'.join(sorted(set(normalize_project_name(f) for f in config['features'])))

        if config.get('dependencies'):
            columns['Dependencies'][i] = '\n'.join(get_normalized_dependencies(config['dependencies']))

        if config.get('env-vars'):
            columns['Environment variables'][i] = '\n'.join(
                '='.join(item) for item in sorted(config['env-vars'].items())
            )

        if config.get('scripts'):
            columns['Scripts'][i] = '\n'.join(sorted(config['scripts']))

        if config.get('description'):
            columns['Description'][i] = config['description'].strip()

    for env_name in envs:
        if env_name not in project_config.envs and env_name not in project_config.matrices:
            app.abort(f'Environment `{env_name}` is not defined by project config')

    env_names = set(envs)

    matrix_columns = {
        'Name': {},
        'Type': {},
        'Envs': {},
        'Features': {},
        'Dependencies': {},
        'Environment variables': {},
        'Scripts': {},
        'Description': {},
    }
    matrix_envs = set()
    for i, (matrix_name, matrix_data) in enumerate(project_config.matrices.items()):
        for env_name in matrix_data['envs']:
            matrix_envs.add(env_name)

        if env_names and matrix_name not in env_names:
            continue

        config = matrix_data['config']
        matrix_columns['Name'][i] = matrix_name
        matrix_columns['Type'][i] = config['type']
        matrix_columns['Envs'][i] = '\n'.join(matrix_data['envs'])
        set_available_columns(matrix_columns)

    standalone_columns = {
        'Name': {},
        'Type': {},
        'Features': {},
        'Dependencies': {},
        'Environment variables': {},
        'Scripts': {},
        'Description': {},
    }
    standalone_envs = (
        (env_name, config)
        for env_name, config in project_config.envs.items()
        if env_names or env_name not in matrix_envs
    )
    for i, (env_name, config) in enumerate(standalone_envs):
        if env_names and env_name not in env_names:
            continue

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
