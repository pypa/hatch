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
@click.option(
    "--all", "-a", "build_all", is_flag=True, help="Build all workspace members defined in the hatch-build environment"
)
@click.pass_obj
def build(
    app: Application, location, targets, hooks_only, no_hooks, ext, clean, clean_hooks_after, clean_only, build_all
):
    """Build a project."""
    if build_all:
        _build_all_members(
            app,
            location=location,
            targets=targets,
            hooks_only=hooks_only,
            no_hooks=no_hooks,
            ext=ext,
            clean=clean,
            clean_hooks_after=clean_hooks_after,
            clean_only=clean_only,
        )
        return

    app.ensure_environment_plugin_dependencies()

    from hatch.config.constants import AppEnvVars
    from hatch.project.constants import BUILD_BACKEND, DEFAULT_BUILD_DIRECTORY
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
                command = _build_command(
                    target,
                    location=location,
                    hooks_only=hooks_only,
                    no_hooks=no_hooks,
                    clean=clean,
                    clean_hooks_after=clean_hooks_after,
                    clean_only=clean_only,
                )

                context = ExecutionContext(app.project.build_env)
                context.add_shell_command(command)
                context.env_vars.update(env_vars)
                app.execute_context(context)


def _build_all_members(
    app: Application,
    *,
    location: str | None,
    targets: tuple[str, ...],
    hooks_only: bool,
    no_hooks: bool,
    ext: bool,
    clean: bool,
    clean_hooks_after: bool,
    clean_only: bool,
) -> None:
    """Build all workspace members defined in the hatch-build environment."""
    app.ensure_environment_plugin_dependencies()

    from hatch.config.constants import AppEnvVars
    from hatch.project.constants import DEFAULT_BUILD_DIRECTORY
    from hatch.utils.fs import Path
    from hatch.utils.runner import ExecutionContext
    from hatch.utils.structures import EnvVars

    if hooks_only and no_hooks:
        app.abort("Cannot use both --hooks-only and --no-hooks options together")

    if ext:
        hooks_only = True
        targets = ("wheel",)
    elif not targets:
        targets = ("sdist", "wheel")

    workspace = app.project.build_env.workspace
    members = workspace.members

    if not members:
        build_dir = Path(location).resolve() if location else None

        env_vars = {}
        if app.verbose:
            env_vars[AppEnvVars.VERBOSE] = str(app.verbosity)
        elif app.quiet:
            env_vars[AppEnvVars.QUIET] = str(abs(app.verbosity))

        with EnvVars(env_vars):
            app.project.prepare_build_environment(targets=[target.split(":")[0] for target in targets])

        from hatch.project.constants import BUILD_BACKEND

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
                    command = _build_command(
                        target,
                        location=location,
                        hooks_only=hooks_only,
                        no_hooks=no_hooks,
                        clean=clean,
                        clean_hooks_after=clean_hooks_after,
                        clean_only=clean_only,
                    )

                    context = ExecutionContext(app.project.build_env)
                    context.add_shell_command(command)
                    context.env_vars.update(env_vars)
                    app.execute_context(context)
        return

    shared_build_dir = Path(location).resolve() if location else app.project.location / DEFAULT_BUILD_DIRECTORY

    root_is_buildable = _root_project_is_buildable(app.project)

    env_vars = {}
    if app.verbose:
        env_vars[AppEnvVars.VERBOSE] = str(app.verbosity)
    elif app.quiet:
        env_vars[AppEnvVars.QUIET] = str(abs(app.verbosity))

    with EnvVars(env_vars):
        if root_is_buildable:
            app.project.prepare_build_environment(targets=[target.split(":")[0] for target in targets])
        else:
            app.project.prepare_environment(app.project.build_env, keep_env=False)

    build_env = app.project.build_env

    projects_to_build: list[tuple[str, Path]] = []

    if root_is_buildable:
        projects_to_build.append((app.project.metadata.name, app.project.location))

    projects_to_build.extend((member.name, member.project.location) for member in members)

    with build_env.get_env_vars():
        for label, project_location in projects_to_build:
            app.display_header(label)

            try:
                with project_location.as_cwd():
                    for target in targets:
                        target_name, _, _ = target.partition(":")

                        command = _build_command(
                            target,
                            location=str(shared_build_dir),
                            hooks_only=hooks_only,
                            no_hooks=no_hooks,
                            clean=clean,
                            clean_hooks_after=clean_hooks_after,
                            clean_only=clean_only,
                        )

                        context = ExecutionContext(build_env)
                        context.add_shell_command(command)
                        context.env_vars.update(env_vars)
                        app.execute_context(context)
            except SystemExit as e:
                app.abort(f"Build failed for workspace member `{label}`", code=e.code or 1)


def _build_command(
    target: str,
    *,
    location: str | None,
    hooks_only: bool,
    no_hooks: bool,
    clean: bool,
    clean_hooks_after: bool,
    clean_only: bool,
) -> list[str]:
    from hatch.project.config import env_var_enabled
    from hatch.project.constants import BuildEnvVars

    command = ["python", "-u", "-m", "hatchling", "build", "--target", target]

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

    return command


def _root_project_is_buildable(project) -> bool:
    import os

    from hatch.utils.toml import load_toml_file

    pyproject_path = os.path.join(str(project.location), "pyproject.toml")
    if not os.path.isfile(pyproject_path):
        return False

    raw_config = load_toml_file(pyproject_path)
    return "project" in raw_config and "build-system" in raw_config
