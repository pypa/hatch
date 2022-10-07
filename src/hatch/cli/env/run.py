import click


def parse_variable_spec(spec):
    variable, _, values = spec.partition('=')
    if variable == 'py':
        variable = 'python'

    parsed_values = set(values.split(',')) if values else set()
    return variable, parsed_values


def select_matrix_environments(environments, included_variables, excluded_variables):
    selected_environments = []
    for env_name, variables in environments.items():
        included = set(variables)
        excluded = set()

        for variable, value in variables.items():
            if variable in excluded_variables:
                excluded_values = excluded_variables[variable]
                if not excluded_values or value in excluded_values:
                    excluded.add(variable)
                    break

            if included_variables:
                if variable not in included_variables:
                    included.remove(variable)
                else:
                    included_values = included_variables[variable]
                    if included_values and value not in included_values:
                        included.remove(variable)

        if included and not excluded:
            selected_environments.append(env_name)

    return selected_environments


def filter_environments(environments, filter_data):
    selected_environments = []
    for env_name, env_data in environments.items():
        for key, value in filter_data.items():
            if key not in env_data or env_data[key] != value:
                break
        else:
            selected_environments.append(env_name)

    return selected_environments


@click.command(short_help='Run commands within project environments')
@click.argument('args', required=True, nargs=-1)
@click.option('--env', '-e', 'env_names', multiple=True, help='The environments to target')
@click.option('--include', '-i', 'included_variable_specs', multiple=True, help='The matrix variables to include')
@click.option('--exclude', '-x', 'excluded_variable_specs', multiple=True, help='The matrix variables to exclude')
@click.option('--filter', '-f', 'filter_json', help='The JSON data used to select environments')
@click.option(
    '--force-continue', is_flag=True, help='Run every command and if there were any errors exit with the first code'
)
@click.option('--ignore-compat', is_flag=True, help='Ignore incompatibility when selecting specific environments')
@click.pass_obj
def run(
    app,
    args,
    env_names,
    included_variable_specs,
    excluded_variable_specs,
    filter_json,
    force_continue,
    ignore_compat,
):
    """
    Run commands within project environments.

    The `-e`/`--env` option overrides the equivalent [root option](#hatch) and the `HATCH_ENV` environment variable.

    If environments provide matrices, then you may use the `-i`/`--include` and `-x`/`--exclude` options to
    select or exclude certain variables, optionally followed by specific comma-separated values.
    For example, if you have the following configuration:

    === ":octicons-file-code-16: pyproject.toml"

        \b
        ```toml
        [[tool.hatch.envs.test.matrix]]
        python = ["39", "310"]
        version = ["42", "3.14", "9000"]
        ```

    === ":octicons-file-code-16: hatch.toml"

        \b
        ```toml
        [[envs.test.matrix]]
        python = ["39", "310"]
        version = ["42", "3.14", "9000"]
        ```

    then running:

    \b
    ```
    hatch env run -i py=310 -x version=9000 test:pytest
    ```

    would execute `pytest` in the environments `test.py310-42` and `test.py310-3.14`.
    Note that `py` may be used as an alias for `python`.
    """
    project = app.project

    included_variables = {}
    excluded_variables = {}
    for specs, variables, display_type in (
        (included_variable_specs, included_variables, 'included'),
        (excluded_variable_specs, excluded_variables, 'excluded'),
    ):
        for spec in specs:
            variable, values = parse_variable_spec(spec)
            if variable in variables:
                app.abort(f'Duplicate {display_type} variable: {variable}')
            variables[variable] = values

    if not env_names:
        env_names = [app.env]
    elif 'system' in env_names:
        project.config.config['envs'] = {
            'system': {
                'type': 'system',
                'skip-install': True,
                'scripts': project.config.scripts,
            }
        }

    # Deduplicate
    env_names = list({env_name: None for env_name in env_names})

    environments = []
    matrix_selected = False
    for env_name in env_names:
        if env_name in project.config.matrices:
            matrix_selected = True
            env_data = project.config.matrices[env_name]['envs']
            if not env_data:
                app.abort(f'No variables defined for matrix: {env_name}')

            environments.extend(select_matrix_environments(env_data, included_variables, excluded_variables))
        else:
            environments.append(env_name)

    if filter_json:
        import json

        filter_data = json.loads(filter_json)
        if not isinstance(filter_data, dict):
            app.abort('The --filter/-f option must be a JSON mapping')

        environments[:] = filter_environments(project.config.envs, filter_data)

    if not environments:
        app.abort('No environments were selected')
    elif not matrix_selected and (included_variables or excluded_variables):
        app.abort(f'Variable selection is unsupported for non-matrix environments: {", ".join(env_names)}')

    should_display_header = app.verbose or matrix_selected or len(environments) > 1

    any_compatible = False
    incompatible = {}
    with project.location.as_cwd():
        for env_name in environments:
            environment = app.get_environment(env_name)

            try:
                environment.check_compatibility()
            except Exception as e:
                if ignore_compat or matrix_selected:
                    incompatible[environment.name] = str(e)
                    continue
                else:
                    app.abort(f'Environment `{env_name}` is incompatible: {e}')

            any_compatible = True
            if should_display_header:
                app.display_header(environment.name)

            if env_name == 'system':
                environment.exists = lambda: True

            app.prepare_environment(environment)
            app.run_shell_commands(
                environment,
                [environment.join_command_args(args)],
                force_continue=force_continue,
                show_code_on_error=False,
            )

    if incompatible:
        num_incompatible = len(incompatible)
        padding = '\n' if any_compatible else ''
        app.display_warning(
            f'{padding}Skipped {num_incompatible} incompatible environment{"s" if num_incompatible > 1 else ""}:'
        )
        for env_name, reason in incompatible.items():
            app.display_warning(f'{env_name} -> {reason}')
