from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application
    from hatch.env.plugin.interface import EnvironmentInterface


@click.command(short_help='Run tests', context_settings={'ignore_unknown_options': True})
@click.argument('args', nargs=-1)
@click.option('--randomize', '-r', is_flag=True, help='Randomize the order of test execution')
@click.option('--parallel', '-p', is_flag=True, help='Parallelize test execution')
@click.option('--retries', type=int, help='Number of times to retry failed tests')
@click.option('--retry-delay', type=float, help='Seconds to wait between retries')
@click.option('--cover', '-c', is_flag=True, help='Measure code coverage')
@click.option('--cover-quiet', is_flag=True, help='Disable coverage reporting after tests, implicitly enabling --cover')
@click.option('--all', '-a', 'test_all', is_flag=True, help='Test all environments in the matrix')
@click.option('--python', '-py', help='The Python versions to test, equivalent to: -i py=...')
@click.option('--include', '-i', 'included_variable_specs', multiple=True, help='The matrix variables to include')
@click.option('--exclude', '-x', 'excluded_variable_specs', multiple=True, help='The matrix variables to exclude')
@click.option('--show', '-s', is_flag=True, help='Show information about environments in the matrix')
@click.pass_context
def test(
    ctx: click.Context,
    *,
    args: tuple[str, ...],
    randomize: bool,
    parallel: bool,
    retries: int | None,
    retry_delay: float | None,
    cover: bool,
    cover_quiet: bool,
    test_all: bool,
    python: str | None,
    included_variable_specs: tuple[str, ...],
    excluded_variable_specs: tuple[str, ...],
    show: bool,
):
    """Run tests using the `hatch-test` environment matrix.

    If no filtering options are selected, then tests will be run in the first compatible environment
    found in the matrix with priority given to those matching the current interpreter.

    The `-i`/`--include` and `-x`/`--exclude` options may be used to include or exclude certain
    variables, optionally followed by specific comma-separated values, and may be selected multiple
    times. For example, if you have the following configuration:

    \b
    ```toml config-example
    [[tool.hatch.envs.hatch-test.matrix]]
    python = ["3.9", "3.10"]
    version = ["42", "3.14", "9000"]
    ```

    then running:

    \b
    ```
    hatch test -i py=3.10 -x version=9000
    ```

    would run tests in the environments `hatch-test.py3.10-42` and `hatch-test.py3.10-3.14`.

    The `-py`/`--python` option is a shortcut for specifying the inclusion `-i py=...`.

    \b
    !!! note
        The inclusion option is treated as an intersection while the exclusion option is treated as a
        union i.e. an environment must match all of the included variables to be selected while matching
        any of the excluded variables will prevent selection.
    """
    app: Application = ctx.obj

    if show:
        import os

        from hatch.cli.env.show import show as show_env

        ctx.invoke(
            show_env,
            internal=True,
            hide_titles=True,
            force_ascii=os.environ.get('HATCH_SELF_TESTING') == 'true',
            envs=ctx.obj.project.config.internal_matrices['hatch-test']['envs'] if app.verbose else ['hatch-test'],
        )
        return

    if cover_quiet:
        cover = True

    import sys

    from hatch.cli.test.core import PatchedCoverageConfig
    from hatch.utils.runner import parse_matrix_variables, select_environments

    if python is not None:
        included_variable_specs = (f'py={python}', *included_variable_specs)

    try:
        included_variables = parse_matrix_variables(included_variable_specs)
    except ValueError as e:
        app.abort(f'Duplicate included variable: {e}')

    try:
        excluded_variables = parse_matrix_variables(excluded_variable_specs)
    except ValueError as e:
        app.abort(f'Duplicate excluded variable: {e}')

    if test_all and (included_variables or excluded_variables):
        app.abort('The --all option cannot be used with the --include or --exclude options.')

    if retries is None and retry_delay is not None:
        app.abort('The --retry-delay option requires the --retries option to be set as well.')

    app.ensure_environment_plugin_dependencies()

    test_envs = app.project.config.internal_matrices['hatch-test']['envs']
    selected_envs: list[str] = []
    multiple_possible = True
    if test_all:
        selected_envs.extend(test_envs)
    elif included_variables or excluded_variables:
        selected_envs.extend(select_environments(test_envs, included_variables, excluded_variables))
    else:
        multiple_possible = False

        # Prioritize candidates that seems to match the running interpreter
        current_version = '.'.join(map(str, sys.version_info[:2]))
        candidate_names: list[str] = list(test_envs)
        candidate_names.sort(key=lambda name: test_envs[name].get('python') != current_version)

        candidate_envs: list[EnvironmentInterface] = []
        for candidate_name in candidate_names:
            environment = app.get_environment(candidate_name)
            if environment.exists():
                selected_envs.append(candidate_name)
                break

            candidate_envs.append(environment)

        if not selected_envs:
            # If none of the candidates exist, then do a check for compatibility
            for candidate_env in candidate_envs:
                try:
                    candidate_env.check_compatibility()
                except Exception:  # noqa: BLE001, S110
                    pass
                else:
                    selected_envs.append(candidate_env.name)
                    break
            else:
                app.abort(f'No compatible environments found: {candidate_envs}')

    test_script = 'run-cov' if cover else 'run'
    patched_coverage = PatchedCoverageConfig(app.project.location, app.data_dir / '.config')
    coverage_config_file = str(patched_coverage.internal_config_path)
    if cover:
        patched_coverage.write_config_file()

    for context in app.runner_context(selected_envs, ignore_compat=multiple_possible, display_header=multiple_possible):
        internal_arguments: list[str] = list(context.env.config.get('extra-args', []))

        if not context.env.config.get('randomize', randomize):
            internal_arguments.extend(['-p', 'no:randomly'])

        if context.env.config.get('parallel', parallel):
            internal_arguments.extend(['-n', 'logical'])

        if (num_retries := context.env.config.get('retries', retries)) is not None:
            if '-r' not in args:
                internal_arguments.extend(['-r', 'aR'])

            internal_arguments.extend(['--reruns', str(num_retries)])

        if (seconds_delay := context.env.config.get('retry-delay', retry_delay)) is not None:
            internal_arguments.extend(['--reruns-delay', str(seconds_delay)])

        internal_args = context.env.join_command_args(internal_arguments)
        if internal_args:
            # Add an extra space if required
            internal_args = f' {internal_args}'

        arguments: list[str] = []
        if args:
            arguments.extend(args)
        else:
            arguments.extend(context.env.config.get('default-args', ['tests']))

        context.add_shell_command([test_script, *arguments])
        context.env_vars['HATCH_TEST_ARGS'] = internal_args
        if cover:
            context.env_vars['COVERAGE_RCFILE'] = coverage_config_file
            context.env_vars['COVERAGE_PROCESS_START'] = coverage_config_file

    if cover:
        for context in app.runner_context([selected_envs[0]]):
            context.add_shell_command('cov-combine')

        if not cover_quiet:
            for context in app.runner_context([selected_envs[0]]):
                context.add_shell_command('cov-report')
