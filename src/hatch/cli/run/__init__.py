import click


def parse_variable_filter(argument):
    variable, _, values = argument[1:].partition('=')
    if variable == 'py':
        variable = 'python'

    parsed_values = set(values.split(',')) if values else set()
    return variable, parsed_values


def select_matrix_environments(environments, included_variables, excluded_variables):
    selected_environments = []
    for env_name, variables in environments.items():
        for variable, value in variables.items():
            if variable in excluded_variables:
                excluded_values = excluded_variables[variable]
                if not excluded_values or value in excluded_values:
                    break

            if included_variables:
                if variable not in included_variables:
                    break
                else:
                    included_values = included_variables[variable]
                    if included_values and value not in included_values:
                        break
        else:
            selected_environments.append(env_name)

    return selected_environments


@click.command(
    short_help='Run commands within project environments',
    context_settings={'help_option_names': [], 'ignore_unknown_options': True},
)
@click.argument('args', metavar='[ENV:]ARGS...', required=True, nargs=-1)
@click.pass_obj
def run(app, args):
    """
    Run commands within project environments.

    If the first argument contains a colon, then the preceding component will be
    interpreted as the name of the environment to target, overriding the `-e`/`--env`
    [root option](#hatch) and the `HATCH_ENV` environment variable.

    If the environment provides matrices, then you may also provide leading arguments
    starting with a `+` or `-` to select or exclude certain variables, optionally
    followed by specific comma-separated values. For example, if you have the
    following configuration:

    === ":octicons-file-code-16: pyproject.toml"

        ```toml
        [[tool.hatch.envs.test.matrix]]
        python = ["39", "310"]
        version = ["42", "3.14", "9000"]
        ```

    === ":octicons-file-code-16: hatch.toml"

        ```toml
        [[envs.test.matrix]]
        python = ["39", "310"]
        version = ["42", "3.14", "9000"]
        ```

    then running:

    ```
    hatch run +py=310 -version=9000 test:pytest
    ```

    would execute `pytest` in the environments `test.py310-42` and `test.py310-3.14`.
    Note that `py` may be used as an alias for `python`.
    """
    project = app.project

    command_start = 0
    included_variables = {}
    excluded_variables = {}
    for i, arg in enumerate(args):
        command_start = i
        if arg.startswith('+'):
            variable, values = parse_variable_filter(arg)
            if variable in included_variables:
                app.abort(f'Duplicate included variable: {variable}')
            included_variables[variable] = values
        elif arg.startswith('-'):
            variable, values = parse_variable_filter(arg)
            if variable in excluded_variables:
                app.abort(f'Duplicate excluded variable: {variable}')
            excluded_variables[variable] = values
        else:
            break
    else:
        command_start += 1

    args = args[command_start:]
    if not args:
        app.abort('Missing argument `MATRIX:ARGS...`')

    command, *args = args
    env_name, separator, command = command.rpartition(':')
    if not separator:
        env_name = app.env

    args = [command, *args]

    system_environment = False
    if not env_name:
        system_environment = True
        env_name = 'system'
        project.config.config['envs'] = {
            env_name: {
                'type': env_name,
                'skip-install': True,
                'scripts': project.config.scripts,
            }
        }

    is_matrix = False
    if env_name in project.config.matrices:
        is_matrix = True
        env_data = project.config.matrices[env_name]['envs']
        if not env_data:
            app.abort(f'No variables defined for matrix: {env_name}')

        environments = select_matrix_environments(env_data, included_variables, excluded_variables)
        if not environments:
            app.abort('No environments were selected')
    else:
        if included_variables or excluded_variables:
            app.abort(f'Variable selection is unsupported for non-matrix environment: {env_name}')

        environments = [env_name]

    any_compatible = False
    incompatible = {}
    with project.location.as_cwd():
        for env_name in environments:
            environment = app.get_environment(env_name)

            try:
                environment.check_compatibility()
            except Exception as e:
                if is_matrix:
                    incompatible[environment.name] = str(e)
                    continue
                else:
                    app.abort(f'Environment `{env_name}` is incompatible: {e}')

            any_compatible = True
            if is_matrix:
                app.display_header(environment.name)

            if system_environment:
                environment.exists = lambda: True

            app.prepare_environment(environment)

            for process in environment.run_shell_commands([environment.join_command_args(args)]):
                if process.returncode:
                    app.abort(code=process.returncode)

    if incompatible:
        num_incompatible = len(incompatible)
        padding = '\n' if any_compatible else ''
        app.display_warning(
            f'{padding}Skipped {num_incompatible} incompatible environment{"s" if num_incompatible > 1 else ""}:'
        )
        for env_name, reason in incompatible.items():
            app.display_warning(f'{env_name} -> {reason}')
