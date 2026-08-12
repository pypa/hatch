from __future__ import annotations

import os
from typing import cast

import click

from hatch._version import __version__
from hatch.cli.lazy import LazyGroup
from hatch.config.constants import AppEnvVars, ConfigEnvVars
from hatch.utils.ci import running_in_ci
from hatch.utils.fs import Path

_LAZY_SUBCOMMANDS = {
    "build": "hatch.cli.build:build",
    "check": "hatch.cli.check:check",
    "clean": "hatch.cli.clean:clean",
    "config": "hatch.cli.config:config",
    "dep": "hatch.cli.dep:dep",
    "env": "hatch.cli.env:env",
    "fmt": "hatch.cli.fmt:fmt",
    "lock": "hatch.cli.lock_cmd:lock_command",
    "new": "hatch.cli.new:new",
    "project": "hatch.cli.project:project",
    "publish": "hatch.cli.publish:publish",
    "python": "hatch.cli.python:python",
    "run": "hatch.cli.run:run",
    "shell": "hatch.cli.shell:shell",
    "status": "hatch.cli.status:status",
    "test": "hatch.cli.test:test",
    "version": "hatch.cli.version:version",
}

@click.group(
    cls=LazyGroup,
    lazy_subcommands=_LAZY_SUBCOMMANDS,
    context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 120},
    invoke_without_command=True,
)
@click.option(
    "--env",
    "-e",
    "env_name",
    envvar=AppEnvVars.ENV,
    default="default",
    help="The name of the environment to use [env var: `HATCH_ENV`]",
)
@click.option(
    "--project",
    "-p",
    envvar=ConfigEnvVars.PROJECT,
    help="The name of the project to work on [env var: `HATCH_PROJECT`]",
)
@click.option(
    "--verbose",
    "-v",
    envvar=AppEnvVars.VERBOSE,
    count=True,
    help="Increase verbosity (can be used additively) [env var: `HATCH_VERBOSE`]",
)
@click.option(
    "--quiet",
    "-q",
    envvar=AppEnvVars.QUIET,
    count=True,
    help="Decrease verbosity (can be used additively) [env var: `HATCH_QUIET`]",
)
@click.option(
    "--color/--no-color",
    default=None,
    help="Whether or not to display colored output (default is auto-detection) [env vars: `FORCE_COLOR`/`NO_COLOR`]",
)
@click.option(
    "--interactive/--no-interactive",
    envvar=AppEnvVars.INTERACTIVE,
    default=None,
    help=(
        "Whether or not to allow features like prompts and progress bars (default is auto-detection) "
        "[env var: `HATCH_INTERACTIVE`]"
    ),
)
@click.option(
    "--data-dir",
    envvar=ConfigEnvVars.DATA,
    help="The path to a custom directory used to persist data [env var: `HATCH_DATA_DIR`]",
)
@click.option(
    "--cache-dir",
    envvar=ConfigEnvVars.CACHE,
    help="The path to a custom directory used to cache data [env var: `HATCH_CACHE_DIR`]",
)
@click.option(
    "--config",
    "config_file",
    envvar=ConfigEnvVars.CONFIG,
    help="The path to a custom config file to use [env var: `HATCH_CONFIG`]",
)
@click.version_option(version=__version__, prog_name="Hatch")
@click.pass_context
def hatch(
    ctx: click.Context,
    env_name,
    project,
    verbose,
    quiet,
    color,
    interactive,
    data_dir,
    cache_dir,
    config_file,
):
    """
    \b
     _   _       _       _
    | | | |     | |     | |
    | |_| | __ _| |_ ___| |__
    |  _  |/ _` | __/ __| '_ \\
    | | | | (_| | || (__| | | |
    \\_| |_/\\__,_|\\__\\___|_| |_|
    """
    if color is None:
        if os.environ.get(AppEnvVars.NO_COLOR) == "1":
            color = False
        elif os.environ.get(AppEnvVars.FORCE_COLOR) == "1":
            color = True

    if interactive is None and running_in_ci():
        interactive = False

    from hatch.cli.application import Application
    from hatch.project.core import Project

    app = Application(ctx.exit, verbosity=verbose - quiet, enable_color=color, interactive=interactive)

    app.env_active = os.environ.get(AppEnvVars.ENV_ACTIVE)
    if (
        app.env_active
        and (param_source := ctx.get_parameter_source("env_name")) is not None
        and param_source.name == "DEFAULT"
    ):
        app.env = app.env_active
    else:
        app.env = env_name

    if config_file:
        app.config_file.path = Path(config_file).resolve()
        if not app.config_file.path.is_file():
            app.abort(f"The selected config file `{app.config_file.path}` does not exist.")
    elif not app.config_file.path.is_file():
        if app.verbose:
            app.display_waiting("No config file found, creating one with default settings now...")

        try:
            app.config_file.restore()
            if app.verbose:
                app.display_success("Success! Please see `hatch config`.")
        except OSError:  # no cov
            app.abort(
                f"Unable to create config file located at `{app.config_file.path}`. Please check your permissions."
            )

    if not ctx.invoked_subcommand:
        app.display_info(ctx.get_help())
        return

    # Persist app data for sub-commands
    ctx.obj = app

    try:
        app.config_file.load()
    except OSError as e:  # no cov
        app.abort(f"Error loading configuration: {e}")

    app.config.terminal.styles.parse_fields()
    errors = app.initialize_styles(app.config.terminal.styles.raw_data)
    if errors and color is not False and not app.quiet:  # no cov
        for error in errors:
            app.display_warning(error)

    app.data_dir = Path(data_dir or app.config.dirs.data).expand()
    app.cache_dir = Path(cache_dir or app.config.dirs.cache).expand()

    if project:
        potential_project = Project.from_config(app.config, project)
        if potential_project is None or potential_project.root is None:
            app.abort(f"Unable to locate project {project}")

        app.project = cast(Project, potential_project)
        app.project.set_app(app)
        return

    app.project = Project(Path.cwd())
    app.project.set_app(app)

    if app.config.mode == "local":
        return

    # The following logic is mostly duplicated for each branch so coverage can be asserted
    if app.config.mode == "project":
        if not app.config.project:
            app.display_warning("Mode is set to `project` but no project is set, defaulting to the current directory")
            return

        possible_project = Project.from_config(app.config, app.config.project)
        if possible_project is None:
            app.display_warning(f"Unable to locate project {app.config.project}, defaulting to the current directory")
        else:
            app.project = possible_project

        app.project.set_app(app)
        return

    if app.config.mode == "aware" and app.project.root is None:
        if not app.config.project:
            app.display_warning("Mode is set to `aware` but no project is set, defaulting to the current directory")
            return

        possible_project = Project.from_config(app.config, app.config.project)
        if possible_project is None:
            app.display_warning(f"Unable to locate project {app.config.project}, defaulting to the current directory")
        else:
            app.project = possible_project

        app.project.set_app(app)
        return


from hatch.cli.self import self_command
hatch.add_command(self_command)

def main():  # no cov
    try:
        hatch(prog_name="hatch", windows_expand_args=False)
    except Exception:  # noqa: BLE001
        import sys

        from rich.console import Console

        console = Console()
        hatch_debug = os.getenv("HATCH_DEBUG") in {"1", "true"}
        console.print_exception(suppress=[click], show_locals=hatch_debug)
        sys.exit(1)
