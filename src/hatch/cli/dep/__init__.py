import click


@click.group(short_help='Manage environment dependencies')
def dep():
    pass


@dep.command('hash', short_help='Output a hash of the currently defined dependencies')
@click.option('--project-only', '-p', is_flag=True, help='Whether or not to exclude environment dependencies')
@click.option('--env-only', '-e', is_flag=True, help='Whether or not to exclude project dependencies')
@click.pass_obj
def hash_dependencies(app, project_only, env_only):
    """Output a hash of the currently defined dependencies."""
    from hashlib import sha256

    from hatch.utils.dep import get_normalized_dependencies

    all_dependencies = []
    if project_only:
        all_dependencies.extend(app.project.metadata.core.dependencies)
    elif env_only:
        environment = app.get_environment()
        all_dependencies.extend(environment.environment_dependencies)
    else:
        all_dependencies.extend(app.project.metadata.core.dependencies)
        environment = app.get_environment()
        all_dependencies.extend(environment.environment_dependencies)

    data = ''.join(
        sorted(
            # Internal spacing is ignored by PEP 440
            dependency.replace(' ', '')
            for dependency in get_normalized_dependencies(all_dependencies)
        )
    ).encode('utf-8')

    app.display_info(sha256(data).hexdigest())


@dep.group(short_help='Display dependencies in various formats')
def show():
    pass


@show.command(short_help='Enumerate dependencies in a tabular format')
@click.option('--project-only', '-p', is_flag=True, help='Whether or not to exclude environment dependencies')
@click.option('--env-only', '-e', is_flag=True, help='Whether or not to exclude project dependencies')
@click.option('--lines', '-l', 'show_lines', is_flag=True, help='Whether or not to show lines between table rows')
@click.option('--ascii', 'force_ascii', is_flag=True, help='Whether or not to only use ASCII characters')
@click.pass_obj
def table(app, project_only, env_only, show_lines, force_ascii):
    """Enumerate dependencies in a tabular format."""
    from packaging.requirements import Requirement

    from hatch.utils.dep import get_normalized_dependencies, normalize_marker_quoting

    project_dependencies = []
    environment_dependencies = []
    if project_only:
        project_dependencies.extend(app.project.metadata.core.dependencies)
    elif env_only:
        environment = app.get_environment()
        environment_dependencies.extend(environment.environment_dependencies)
    else:
        project_dependencies.extend(app.project.metadata.core.dependencies)

        environment = app.get_environment()
        environment_dependencies.extend(environment.environment_dependencies)

    for dependencies, table_title in (
        (project_dependencies, 'Project'),
        (environment_dependencies, f'Env: {app.env}'),
    ):
        if not dependencies:
            continue

        requirements = [Requirement(d) for d in get_normalized_dependencies(dependencies)]

        columns = {'Name': {}, 'URL': {}, 'Versions': {}, 'Markers': {}, 'Features': {}}
        for i, requirement in enumerate(requirements):
            columns['Name'][i] = requirement.name

            if requirement.url:
                columns['URL'][i] = str(requirement.url)

            if requirement.specifier:
                columns['Versions'][i] = str(requirement.specifier)

            if requirement.marker:
                columns['Markers'][i] = normalize_marker_quoting(str(requirement.marker))

            if requirement.extras:
                columns['Features'][i] = ', '.join(sorted(requirement.extras))

        column_options = {}
        for column_title in columns:
            if column_title != 'URL':
                column_options[column_title] = {'no_wrap': True}

        app.display_table(
            table_title, columns, show_lines=show_lines, column_options=column_options, force_ascii=force_ascii
        )


@show.command(short_help='Enumerate dependencies as a list of requirements')
@click.option('--project-only', '-p', is_flag=True, help='Whether or not to exclude environment dependencies')
@click.option('--env-only', '-e', is_flag=True, help='Whether or not to exclude project dependencies')
@click.option(
    '--feature',
    '-f',
    'features',
    multiple=True,
    help='Whether or not to only show the dependencies of the specified features',
)
@click.option('--all', 'all_features', is_flag=True, help='Whether or not to include the dependencies of all features')
@click.pass_obj
def requirements(app, project_only, env_only, features, all_features):
    """Enumerate dependencies as a list of requirements."""
    from hatch.utils.dep import get_normalized_dependencies
    from hatchling.metadata.utils import normalize_project_name

    dependencies = []
    if features:
        for feature in features:
            feature = normalize_project_name(feature)
            if feature not in app.project.metadata.core.optional_dependencies:
                app.abort(f'Feature `{feature}` is not defined in field `project.optional-dependencies`')

            dependencies.extend(app.project.metadata.core.optional_dependencies[feature])
    elif project_only:
        dependencies.extend(app.project.metadata.core.dependencies)
    elif env_only:
        environment = app.get_environment()
        dependencies.extend(environment.environment_dependencies)
    else:
        dependencies.extend(app.project.metadata.core.dependencies)

        environment = app.get_environment()
        dependencies.extend(environment.environment_dependencies)

    if not features and all_features:
        for optional_dependencies in app.project.metadata.core.optional_dependencies.values():
            dependencies.extend(optional_dependencies)

    for dependency in get_normalized_dependencies(dependencies):
        app.display_info(dependency)
