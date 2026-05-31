from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help="Type check source code", context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1)
@click.option("--summarize", "-s", is_flag=True, help="Include error summary statistics")
@click.option("--cover", is_flag=True, help="Generate a type coverage report")
@click.pass_obj
def types(
    app: Application,
    *,
    args: tuple[str, ...],
    summarize: bool,
    cover: bool,
):
    """
    Type check source code, using Pyrefly by default.
    """
    from hatch.cli.types.core import TypeCheckEnvironment

    app.ensure_environment_plugin_dependencies()

    for context in app.runner_context(["hatch-check-types"]):
        tc_env = TypeCheckEnvironment(context.env)

        if cover:
            script = "coverage"
        elif summarize:
            script = "check-summarize"
        else:
            script = "check"

        default_args = tc_env.get_default_args()
        internal_args = context.env.join_command_args(default_args)
        if internal_args:
            internal_args = f" {internal_args}"

        formatted_args = context.env.join_command_args(list(args))
        context.add_shell_command(f"{script} {formatted_args}")

        context.env_vars["HATCH_CHECK_TYPES_ARGS"] = internal_args

        if not tc_env.config_path:
            tc_env.write_config_file()
