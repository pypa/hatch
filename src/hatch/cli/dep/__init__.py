import click


def get_unique_dependencies(all_dependencies):
    dependencies = set()
    for dependency in all_dependencies:
        # Remove any surrounding white space
        dependency = dependency.strip()
        # Internal spacing is ignored by PEP 440
        dependency = dependency.replace(' ', '')
        # Normalize casing
        dependency = dependency.lower()

        dependencies.add(dependency)

    return dependencies


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

    data = ''.join(sorted(get_unique_dependencies(all_dependencies))).encode('utf-8')

    app.display_info(sha256(data).hexdigest())


@dep.group(short_help='Display dependencies in various formats')
def show():
    pass


@show.command(short_help='Enumerate dependencies in a tabular format')
@click.option('--project-only', '-p', is_flag=True, help='Whether or not to exclude environment dependencies')
@click.option('--env-only', '-e', is_flag=True, help='Whether or not to exclude project dependencies')
@click.option('--lines', '-l', 'show_lines', is_flag=True, help='Whether or not to show lines between table rows')
@click.pass_obj
def table(app, project_only, env_only, show_lines):
    """Enumerate dependencies in a tabular format."""
    from packaging.requirements import Requirement
    from rich.table import Table

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

    for dependencies, title in (
        (project_dependencies, 'Project'),
        (environment_dependencies, f'Environment: {app.env}'),
    ):
        if not dependencies:
            continue

        dependency_table = Table(title=title, show_lines=show_lines)

        # There will always be a name
        dependency_table.add_column('Name', style='bold', no_wrap=True)

        requirements = sorted((Requirement(d) for d in get_unique_dependencies(dependencies)), key=lambda r: r.name)

        potential_attributes = {'url': False, 'specifier': False, 'marker': False, 'extras': False}
        attribute_titles = {'url': 'URL', 'specifier': 'Versions', 'marker': 'Markers', 'extras': 'Features'}

        for requirement in requirements:
            for attribute in potential_attributes:
                if getattr(requirement, attribute):
                    potential_attributes[attribute] = True

        present_attributes = []
        for attribute, present in potential_attributes.items():
            if present:
                present_attributes.append(attribute)
                dependency_table.add_column(attribute_titles[attribute], style='bold', no_wrap=attribute != 'url')

        for requirement in requirements:
            attributes = [requirement.name]
            for attribute in present_attributes:
                value = getattr(requirement, attribute)
                if not value:
                    value = ''
                elif attribute == 'extras':
                    value = ', '.join(sorted(value))
                else:
                    value = str(value)

                attributes.append(value)

            dependency_table.add_row(*attributes)

        app.display(dependency_table)
