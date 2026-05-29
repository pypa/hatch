from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help="Perform static analysis", context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1)
@click.option("--fix", is_flag=True, help="Fix lint errors rather than just reporting them")
@click.option("--sync", is_flag=True, help="Sync the default config file with the current version of Hatch")
@click.pass_obj
def code(
    app: Application,
    *,
    args: tuple[str, ...],
    fix: bool,
    sync: bool,
):
    """
    Perform static analysis, using Ruff by default.
    """
    from hatch.cli.fmt.core import StaticAnalysisEnvironment

    app.ensure_environment_plugin_dependencies()

    for context in app.runner_context(["hatch-static-analysis"]):
        sa_env = StaticAnalysisEnvironment(context.env)

        # TODO: remove in a few minor releases, this is very new but we don't want to break users on the cutting edge
        if legacy_config_path := app.project.config.config.get("format", {}).get("config-path", ""):
            app.display_warning(
                "The `tool.hatch.format.config-path` option is deprecated and will be removed in a future release. "
                "Use `tool.hatch.envs.hatch-static-analysis.config-path` instead."
            )
            sa_env.config_path = legacy_config_path

        if sync and not sa_env.config_path:
            app.abort("The --sync flag can only be used when the `tool.hatch.format.config-path` option is defined")

        script = "lint-fix" if fix else "lint-check"

        default_args = sa_env.get_default_args()
        arguments = list(args)
        try:
            arguments.remove("--preview")
        except ValueError:
            preview = False
        else:
            preview = True
            default_args.append("--preview")

        internal_args = context.env.join_command_args(default_args)
        if internal_args:
            internal_args = f" {internal_args}"

        formatted_args = context.env.join_command_args(arguments)
        context.add_shell_command(f"{script} {formatted_args}")

        context.env_vars["HATCH_FMT_ARGS"] = internal_args

        if not sa_env.config_path or sync:
            sa_env.write_config_file(preview=preview)
