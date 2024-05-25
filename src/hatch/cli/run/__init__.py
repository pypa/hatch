from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(
    short_help='Run commands within project environments',
    context_settings={'help_option_names': [], 'ignore_unknown_options': True},
)
@click.argument('args', metavar='[ENV:]ARGS...', required=True, nargs=-1)
@click.pass_context
def run(ctx: click.Context, args: tuple[str, ...]):
    """
    Run commands within project environments.
    This is a convenience wrapper around the [`env run`](#hatch-env-run) command.

    If the first argument contains a colon, then the preceding component will be
    interpreted as the name of the environment to target, overriding the `-e`/`--env`
    [root option](#hatch) and the `HATCH_ENV` environment variable.

    If the environment provides matrices, then you may also provide leading arguments
    starting with a `+` or `-` to select or exclude certain variables, optionally
    followed by specific comma-separated values. For example, if you have the
    following configuration:

    \b
    ```toml tab="pyproject.toml"
    [[tool.hatch.envs.test.matrix]]
    python = ["3.9", "3.10"]
    version = ["42", "3.14", "9000"]
    ```

    ```toml tab="hatch.toml"
    [[envs.test.matrix]]
    python = ["3.9", "3.10"]
    version = ["42", "3.14", "9000"]
    ```

    then running:

    \b
    ```
    hatch run +py=3.10 -version=9000 test:pytest
    ```

    would execute `pytest` in the environments `test.py3.10-42` and `test.py3.10-3.14`.
    Note that `py` may be used as an alias for `python`.

    \b
    !!! note
        Inclusions are treated as an intersection while exclusions are treated as a union i.e.
        an environment must match all of the included variables to be selected while matching
        any of the excluded variables will prevent selection.
    """
    app: Application = ctx.obj

    first_arg = args[0]
    if first_arg in {'-h', '--help'}:
        app.display_info(ctx.get_help())
        return

    from hatch.utils.fs import Path

    if first_arg.endswith('.py') and (script := Path(first_arg)).is_file():
        from hatch.project.utils import parse_inline_script_metadata

        # Ensure consistent IDs for storage
        script = script.resolve()

        try:
            metadata = parse_inline_script_metadata(script.read_text())
        except ValueError as e:
            app.abort(f'{e}, {first_arg}')

        # Ignore scripts that don't define metadata blocks or define empty metadata blocks
        if metadata:
            from hatch.env.utils import ensure_valid_environment

            config = metadata.get('tool', {}).get('hatch', {})
            config['skip-install'] = True
            config.setdefault('installer', 'uv')
            config.setdefault('dependencies', [])
            config['dependencies'].extend(metadata.get('dependencies', []))

            if 'python' not in config and (requires_python := metadata.get('requires-python')) is not None:
                import re
                import sys

                from packaging.specifiers import SpecifierSet

                from hatch.python.distributions import DISTRIBUTIONS

                current_version = '.'.join(map(str, sys.version_info[:2]))
                distributions = [name for name in DISTRIBUTIONS if re.match(r'^\d+\.\d+$', name)]
                distributions.sort(key=lambda name: name != current_version)

                python_constraint = SpecifierSet(requires_python)
                for distribution in distributions:
                    # Try an artificially high patch version to account for
                    # common cases like `>=3.11.4` or `>=3.10,<3.11`
                    if python_constraint.contains(f'{distribution}.100'):
                        config['python'] = distribution
                        break
                else:
                    app.abort(f'Unable to satisfy Python version constraint: {requires_python}')

            ensure_valid_environment(config)
            app.project.config.envs[script.id] = config
            app.project.set_path(script)
            for context in app.runner_context([script.id]):
                context.add_shell_command(['python', first_arg, *args[1:]])

            return

    from hatch.cli.env.run import run as run_command

    command_start = 0
    included_variables = []
    excluded_variables = []
    for i, arg in enumerate(args):
        command_start = i
        if arg.startswith('+'):
            included_variables.append(arg[1:])
        elif arg.startswith('-'):
            excluded_variables.append(arg[1:])
        else:
            break
    else:
        command_start += 1

    args = args[command_start:]
    if not args:
        app.abort('Missing argument `MATRIX:ARGS...`')

    command, *final_args = args
    env_name, separator, command = command.rpartition(':')
    if not separator:
        env_name = app.env
    elif not env_name:
        env_name = 'system'

    ctx.invoke(
        run_command,
        args=[command, *final_args],
        env_names=[env_name],
        included_variable_specs=included_variables,
        excluded_variable_specs=excluded_variables,
    )
