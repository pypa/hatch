import click

from hatch.cli.env.run import prepare_and_optionally_run


@click.group(short_help='Manage environment dependencies')
def dep():
    pass


@dep.command('hash', short_help='Output a hash of the currently defined dependencies')
@click.option('--project-only', '-p', is_flag=True, help='Whether or not to exclude environment dependencies')
@click.option('--env-only', '-e', is_flag=True, help='Whether or not to exclude project dependencies')
@click.pass_obj
def hash_dependencies(app, project_only, env_only):
    """Output a hash of the currently defined dependencies."""
    app.ensure_environment_plugin_dependencies()

    from hatch.utils.dep import get_project_dependencies_complex, hash_dependencies

    environment = app.get_environment()

    all_requirements = []
    if project_only:
        dependencies_complex, _ = get_project_dependencies_complex(environment)
        all_requirements.extend(dependencies_complex.values())
    elif env_only:
        all_requirements.extend(environment.environment_dependencies_complex)
    else:
        dependencies_complex, _ = get_project_dependencies_complex(environment)
        all_requirements.extend(dependencies_complex.values())
        all_requirements.extend(environment.environment_dependencies_complex)

    app.display(hash_dependencies(all_requirements))


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
    app.ensure_environment_plugin_dependencies()

    from packaging.requirements import Requirement

    from hatch.utils.dep import get_normalized_dependencies, get_project_dependencies_complex, normalize_marker_quoting

    environment = app.get_environment()

    project_requirements = []
    environment_requirements = []
    if project_only:
        dependencies_complex, _ = get_project_dependencies_complex(environment)
        project_requirements.extend(dependencies_complex.values())
    elif env_only:
        environment_requirements.extend(environment.environment_dependencies_complex)
    else:
        dependencies_complex, _ = get_project_dependencies_complex(environment)
        project_requirements.extend(dependencies_complex.values())
        environment_requirements.extend(environment.environment_dependencies_complex)

    for all_requirements, table_title in (
        (project_requirements, 'Project'),
        (environment_requirements, f'Env: {app.env}'),
    ):
        if not all_requirements:
            continue

        normalized_requirements = [Requirement(d) for d in get_normalized_dependencies(all_requirements)]

        columns = {'Name': {}, 'URL': {}, 'Versions': {}, 'Markers': {}, 'Features': {}}
        for i, requirement in enumerate(normalized_requirements):
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
    app.ensure_environment_plugin_dependencies()

    from hatch.utils.dep import get_normalized_dependencies, get_project_dependencies_complex
    from hatchling.metadata.utils import normalize_project_name

    environment = app.get_environment()
    dependencies_complex, optional_dependencies_complex = get_project_dependencies_complex(environment)

    all_requirements = []
    if features:
        for raw_feature in features:
            feature = normalize_project_name(raw_feature)
            if feature not in optional_dependencies_complex:
                app.abort(f'Feature `{feature}` is not defined in field `project.optional-dependencies`')

            all_requirements.extend(optional_dependencies_complex[feature].values())
    elif project_only:
        all_requirements.extend(dependencies_complex.values())
    elif env_only:
        all_requirements.extend(environment.environment_dependencies_complex)
    else:
        all_requirements.extend(dependencies_complex.values())
        all_requirements.extend(environment.environment_dependencies_complex)

    if not features and all_features:
        for optional_dependencies in optional_dependencies_complex.values():
            all_requirements.extend(optional_dependencies.values())

    for dependency in get_normalized_dependencies(all_requirements):
        app.display(dependency)


@dep.command(short_help='Sync the latest dependencies into project environments')
@click.option('--env', '-e', 'env_names', multiple=True, help='The environments to target')
@click.option('--all', '-a', 'sync_all', is_flag=True, help='Sync all environments')
@click.option(
    '--matrix/--no-matrix', is_flag=True, default=False, help='Used with `--all` to exclude matrix environments'
)
@click.option('--include', '-i', 'included_variable_specs', multiple=True, help='The matrix variables to include')
@click.option('--exclude', '-x', 'excluded_variable_specs', multiple=True, help='The matrix variables to exclude')
@click.option('--filter', '-f', 'filter_json', help='The JSON data used to select environments')
@click.option('--ignore-compat', is_flag=True, help='Ignore incompatibility when selecting specific environments')
@click.pass_obj
def sync(
    app,
    env_names,
    included_variable_specs,
    excluded_variable_specs,
    filter_json,
    ignore_compat,
    sync_all,
    matrix,
):
    """
    Sync the dependencies within a project environment

    The `-e`/`--env` option overrides the equivalent [root option](#hatch) and the `HATCH_ENV` environment variable.

    You can also use the `--all` option to sync all environments. You can optionally
    combine this with the `--matrix` option to include matrix environments.

    \b
    ```
    hatch dep sync --all --matrix
    ```

    If environments provide matrices, then you may use the `-i`/`--include` and `-x`/`--exclude` options to
    select or exclude certain variables, optionally followed by specific comma-separated values.
    For example, if you have the following configuration:

    \b
    ```toml config-example
    [[tool.hatch.envs.test.matrix]]
    python = ["3.9", "3.10"]
    version = ["42", "3.14", "9000"]
    ```

    then running:

    \b
    ```
    hatch dep sync -i py=3.10 -x version=9000
    ```

    would sync the environments `test.py3.10-42` and `test.py3.10-3.14`.
    Note that `py` may be used as an alias for `python`.
    """
    prepare_and_optionally_run(
        app=app,
        env_names=env_names,
        included_variable_specs=included_variable_specs,
        excluded_variable_specs=excluded_variable_specs,
        filter_json=filter_json,
        ignore_compat=ignore_compat,
        args=None,
        force_continue=None,
        exclude_matrix=not matrix,
        run_all=sync_all,
    )
