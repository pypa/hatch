from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application
    from hatch.project.core import Project


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
    "--all",
    "-a",
    "build_all",
    is_flag=True,
    help=(
        "Whether or not to build the workspace root and every workspace member defined by the selected "
        "environment. Artifacts are written to the workspace root's `dist` directory by default"
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
def build(
    app: Application, location, targets, build_all, hooks_only, no_hooks, ext, clean, clean_hooks_after, clean_only
):
    """Build a project."""
    app.ensure_environment_plugin_dependencies()

    from hatch.config.constants import AppEnvVars
    from hatch.project.constants import DEFAULT_BUILD_DIRECTORY
    from hatch.utils.fs import Path

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

    if not build_all:
        _build_project(
            app,
            app.project,
            location,
            targets,
            hooks_only=hooks_only,
            no_hooks=no_hooks,
            clean=clean,
            clean_hooks_after=clean_hooks_after,
            clean_only=clean_only,
            env_vars=env_vars,
        )
        return

    environment = app.project.get_environment()
    members = environment.workspace.members
    if not members:
        app.abort(
            f"The `--all` flag requires workspace members to be defined in field "
            f"`tool.hatch.envs.{environment.name}.workspace.members`"
        )

    # Artifacts from every project are consolidated in a single directory, defaulting to the
    # workspace root. The location must be absolute because each member builds from its own path
    build_directory = str(Path(location).resolve() if location else app.project.location / DEFAULT_BUILD_DIRECTORY)

    # The workspace root is built without needing to be listed as a member, but only when it
    # defines a project itself rather than merely being a container for workspace configuration
    projects = [app.project] if app.project.defines_project else []
    projects.extend(member.project for member in members if member.project.location != app.project.location)
    for project in projects:
        if not clean_only:
            app.display_header(project.metadata.name)

        _build_project(
            app,
            project,
            build_directory,
            targets,
            hooks_only=hooks_only,
            no_hooks=no_hooks,
            clean=clean,
            clean_hooks_after=clean_hooks_after,
            clean_only=clean_only,
            env_vars=env_vars,
        )


def _build_project(
    app: Application,
    project: Project,
    location,
    targets,
    *,
    hooks_only,
    no_hooks,
    clean,
    clean_hooks_after,
    clean_only,
    env_vars,
):
    from hatch.project.config import env_var_enabled
    from hatch.project.constants import BUILD_BACKEND, DEFAULT_BUILD_DIRECTORY, BuildEnvVars
    from hatch.utils.fs import Path
    from hatch.utils.runner import ExecutionContext
    from hatch.utils.structures import EnvVars

    build_dir = Path(location).resolve() if location else None
    target_list = list(targets)
    build_backend = project.metadata.build.build_backend
    target_names = [target.partition(":")[0] for target in target_list]
    build_wheel_via_sdist = (
        build_backend == BUILD_BACKEND
        and not clean_only
        and not hooks_only
        and "sdist" in target_names
        and "wheel" in target_names
    )
    if build_wheel_via_sdist:
        # Always produce the sdist before the wheel so the wheel can be built from it.
        target_list = [target for target in target_list if target.partition(":")[0] != "wheel"] + [
            target for target in target_list if target.partition(":")[0] == "wheel"
        ]

    with EnvVars(env_vars):
        project.prepare_build_environment(targets=[target.split(":")[0] for target in target_list])

    sdist_artifact = None
    with project.location.as_cwd(), project.build_env.get_env_vars():
        for target in target_list:
            target_name, _, _ = target.partition(":")
            if not clean_only:
                app.display_header(target_name)

            if build_backend != BUILD_BACKEND:
                if target_name == "sdist":
                    directory = build_dir or project.location / DEFAULT_BUILD_DIRECTORY
                    directory.ensure_dir_exists()
                    artifact_path = project.build_frontend.build_sdist(directory)
                elif target_name == "wheel":
                    directory = build_dir or project.location / DEFAULT_BUILD_DIRECTORY
                    directory.ensure_dir_exists()
                    artifact_path = project.build_frontend.build_wheel(directory)
                else:
                    app.abort(f"Target `{target_name}` is not supported by `{build_backend}`")

                app.display_info(
                    str(artifact_path.relative_to(project.location))
                    if project.location in artifact_path.parents
                    else str(artifact_path)
                )
            else:
                command = ["python", "-u", "-m", "hatchling", "build", "--target", target]
                command_env = dict(env_vars)

                # We deliberately pass the location unchanged so that absolute paths may be non-local
                # and reflect wherever builds actually take place
                if location:
                    command.extend(("--directory", str(location)))
                elif build_wheel_via_sdist and target_name == "wheel" and sdist_artifact is not None:
                    # Keep the wheel alongside the sdist in the original project dist directory.
                    command.extend(("--directory", str((project.location / DEFAULT_BUILD_DIRECTORY).resolve())))

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

                if build_wheel_via_sdist and target_name == "wheel" and sdist_artifact is not None:
                    from tempfile import TemporaryDirectory

                    from hatchling.builders.sdist_wheel import unpack_sdist

                    with TemporaryDirectory() as temp_dir:
                        project_root = Path(unpack_sdist(str(sdist_artifact), temp_dir))
                        context = ExecutionContext(project.build_env)
                        context.add_shell_command(command)
                        context.env_vars.update(command_env)
                        with project_root.as_cwd():
                            app.execute_context(context)
                else:
                    context = ExecutionContext(project.build_env)
                    context.add_shell_command(command)
                    context.env_vars.update(command_env)
                    app.execute_context(context)

                if target_name == "sdist":
                    dist_directory = build_dir or project.location / DEFAULT_BUILD_DIRECTORY
                    if dist_directory.is_dir():
                        sdists = sorted(dist_directory.glob("*.tar.gz"), key=lambda path: path.stat().st_mtime)
                        if sdists:
                            sdist_artifact = sdists[-1]
