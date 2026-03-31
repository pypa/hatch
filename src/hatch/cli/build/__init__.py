from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help="Build a project")
@click.argument("location", required=False)
@click.option(
    "--target",
    "-t",
    "targets",
    multiple=True,
    help=(
        "The target to build, overriding project defaults. This may be selected multiple times e.g. `-t sdist -t wheel`"
    ),
)
@click.option(
    "--hooks-only", is_flag=True, help="Whether or not to only execute build hooks [env var: `HATCH_BUILD_HOOKS_ONLY`]"
)
@click.option(
    "--no-hooks", is_flag=True, help="Whether or not to disable build hooks [env var: `HATCH_BUILD_NO_HOOKS`]"
)
@click.option(
    "--ext",
    is_flag=True,
    help=(
        "Whether or not to only execute build hooks for distributing binary Python packages, such as "
        "compiling extensions. Equivalent to `--hooks-only -t wheel`"
    ),
)
@click.option(
    "--clean",
    "-c",
    is_flag=True,
    help="Whether or not existing artifacts should first be removed [env var: `HATCH_BUILD_CLEAN`]",
)
@click.option(
    "--clean-hooks-after",
    is_flag=True,
    help=(
        "Whether or not build hook artifacts should be removed after each build "
        "[env var: `HATCH_BUILD_CLEAN_HOOKS_AFTER`]"
    ),
)
@click.option("--clean-only", is_flag=True, hidden=True)
@click.pass_obj
def build(app: Application, location, targets, hooks_only, no_hooks, ext, clean, clean_hooks_after, clean_only):
    """Build a project."""
    app.ensure_environment_plugin_dependencies()

    from hatch.config.constants import AppEnvVars
    from hatch.project.config import env_var_enabled
    from hatch.project.constants import BUILD_BACKEND, DEFAULT_BUILD_DIRECTORY, BuildEnvVars
    from hatch.utils.fs import Path
    from hatch.utils.runner import ExecutionContext
    from hatch.utils.structures import EnvVars

    build_dir = Path(location).resolve() if location else None
    if ext:
        hooks_only = True
        targets = ("wheel",)
    elif not targets:
        targets = ("sdist", "wheel")

    env_vars = {}
    if app.verbose:
        env_vars[AppEnvVars.VERBOSE] = str(app.verbosity)
    elif app.quiet:
        env_vars[AppEnvVars.QUIET] = str(abs(app.verbosity))

    with EnvVars(env_vars):
        app.project.prepare_build_environment(targets=[target.split(":")[0] for target in targets])

    build_backend = app.project.metadata.build.build_backend
    with app.project.location.as_cwd(), app.project.build_env.get_env_vars():
        for target in targets:
            target_name, _, _ = target.partition(":")
            if not clean_only:
                app.display_header(target_name)

            if build_backend != BUILD_BACKEND:
                if target_name == "sdist":
                    directory = build_dir or app.project.location / DEFAULT_BUILD_DIRECTORY
                    directory.ensure_dir_exists()
                    artifact_path = app.project.build_frontend.build_sdist(directory)
                elif target_name == "wheel":
                    directory = build_dir or app.project.location / DEFAULT_BUILD_DIRECTORY
                    directory.ensure_dir_exists()
                    artifact_path = app.project.build_frontend.build_wheel(directory)
                else:
                    app.abort(f"Target `{target_name}` is not supported by `{build_backend}`")

                app.display_info(
                    str(artifact_path.relative_to(app.project.location))
                    if app.project.location in artifact_path.parents
                    else str(artifact_path)
                )
            else:
                command = ["python", "-u", "-m", "hatchling", "build", "--target", target]

                # We deliberately pass the location unchanged so that absolute paths may be non-local
                # and reflect wherever builds actually take place
                if location:
                    command.extend(("--directory", location))

                if hooks_only or env_var_enabled(BuildEnvVars.HOOKS_ONLY):
                    command.append("--hooks-only")

                if no_hooks or env_var_enabled(BuildEnvVars.NO_HOOKS):
                    command.append("--no-hooks")

                if clean or env_var_enabled(BuildEnvVars.CLEAN):
                    command.append("--clean")

                if clean_hooks_after or env_var_enabled(BuildEnvVars.CLEAN_HOOKS_AFTER):
                    command.append("--clean-hooks-after")

                if clean_only:
                    command.append("--clean-only")

                context = ExecutionContext(app.project.build_env)
                context.add_shell_command(command)
                context.env_vars.update(env_vars)
                app.execute_context(context)
