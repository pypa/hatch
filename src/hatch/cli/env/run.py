from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


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
    app: Application,
    *,
    args: tuple[str, ...],
    env_names: tuple[str, ...],
    included_variable_specs: tuple[str, ...],
    excluded_variable_specs: tuple[str, ...],
    filter_json: str | None,
    force_continue: bool,
    ignore_compat: bool,
):
    """
    Run commands within project environments.

    The `-e`/`--env` option overrides the equivalent [root option](#hatch) and the `HATCH_ENV` environment variable.

    The `-i`/`--include` and `-x`/`--exclude` options may be used to include or exclude certain
    variables, optionally followed by specific comma-separated values, and may be selected multiple
    times. For example, if you have the following configuration:

    \b
    ```toml config-example
    [[tool.hatch.envs.test.matrix]]
    python = ["3.9", "3.10"]
    version = ["42", "3.14", "9000"]
    ```

    then running:

    \b
    ```
    hatch env run -i py=3.10 -x version=9000 test:pytest
    ```

    would execute `pytest` in the environments `test.py3.10-42` and `test.py3.10-3.14`.
    Note that `py` may be used as an alias for `python`.

    \b
    !!! note
        The inclusion option is treated as an intersection while the exclusion option is treated as a
        union i.e. an environment must match all of the included variables to be selected while matching
        any of the excluded variables will prevent selection.
    """
    from hatch.utils.runner import parse_matrix_variables, select_environments

    try:
        included_variables = parse_matrix_variables(included_variable_specs)
    except ValueError as e:
        app.abort(f'Duplicate included variable: {e}')

    try:
        excluded_variables = parse_matrix_variables(excluded_variable_specs)
    except ValueError as e:
        app.abort(f'Duplicate excluded variable: {e}')

    app.ensure_environment_plugin_dependencies()

    project = app.project

    if not env_names:
        env_names = (app.env,)
    elif 'system' in env_names:
        project.config.config['envs'] = {
            'system': {
                'type': 'system',
                'skip-install': True,
                'scripts': project.config.scripts,
            }
        }

    # Deduplicate
    ordered_env_names = list(dict.fromkeys(env_names))

    environments = []
    matrix_selected = False
    for env_name in ordered_env_names:
        if env_name in project.config.matrices:
            matrix_selected = True
            env_data = project.config.matrices[env_name]['envs']
            if not env_data:
                app.abort(f'No variables defined for matrix: {env_name}')

            environments.extend(select_environments(env_data, included_variables, excluded_variables))
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
        app.abort(f'Variable selection is unsupported for non-matrix environments: {", ".join(ordered_env_names)}')

    for context in app.runner_context(
        environments,
        ignore_compat=ignore_compat or matrix_selected,
        display_header=matrix_selected,
    ):
        if context.env.name == 'system':
            context.env.exists = lambda: True  # type: ignore[method-assign]

        context.force_continue = force_continue
        context.add_shell_command(list(args))
