from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help="Generate lockfiles for environments")
@click.argument("env_name", required=False, default=None)
@click.option("--all", "lock_all", is_flag=True, help="Lock all environments regardless of config")
@click.option("--upgrade", "-U", is_flag=True, help="Upgrade all packages")
@click.option("--upgrade-package", "-P", multiple=True, help="Upgrade specific package(s)")
@click.option("--export", "export_path", type=click.Path(), default=None, help="Export lockfile to a custom path")
@click.option("--check", is_flag=True, help="Check if lockfile is up-to-date")
@click.pass_obj
def lock(
    app: Application,
    *,
    env_name: str | None,
    lock_all: bool,
    upgrade: bool,
    upgrade_package: tuple[str, ...],
    export_path: str | None,
    check: bool,
):
    """Generate lockfiles for environments.

    When called without arguments, locks all environments that have `locked = true`
    in their configuration. When called with ENV_NAME, locks that specific environment.
    """
    app.ensure_environment_plugin_dependencies()

    from hatch.env.lock import generate_lockfile, resolve_lockfile_path

    if lock_all:
        env_names = [*app.project.config.envs, *app.project.config.internal_envs]
    elif env_name is not None:
        env_names = app.project.expand_environments(env_name)
        if not env_names:
            app.abort(f"Environment `{env_name}` is not defined by project config")
    else:
        # No argument: lock all environments with locked = true
        env_names = []
        for name in app.project.config.envs:
            environment = app.project.get_environment(name)
            if environment.locked:
                env_names.append(name)
        for name in app.project.config.internal_envs:
            environment = app.project.get_environment(name)
            if environment.locked:
                env_names.append(name)

        if not env_names:
            app.abort("No environments are configured with `locked = true`")

    incompatible = {}
    for env in env_names:
        environment = app.project.get_environment(env)

        try:
            environment.check_compatibility()
        except Exception as e:  # noqa: BLE001
            if env_name is None or env_name in app.project.config.matrices:
                incompatible[env] = str(e)
                continue

            app.abort(f"Environment `{env}` is incompatible: {e}")

        if export_path:
            from hatch.utils.fs import Path

            output_path = Path(export_path)
        else:
            output_path = resolve_lockfile_path(environment)

        if check:
            if not output_path.is_file():
                app.abort(f"Lockfile does not exist: {output_path}")
            app.display(f"Lockfile exists: {output_path}")
            continue

        if not environment.dependencies:
            app.display_warning(f"Environment `{env}` has no dependencies to lock")
            continue

        with app.status(f"Locking environment: {env}"):
            generate_lockfile(
                environment,
                output_path,
                upgrade=upgrade,
                upgrade_packages=upgrade_package,
            )

        app.display(f"Wrote lockfile: {output_path}")

    if incompatible:
        num_incompatible = len(incompatible)
        app.display_warning(
            f"Skipped {num_incompatible} incompatible environment{'s' if num_incompatible > 1 else ''}:"
        )
        for env, reason in incompatible.items():
            app.display_warning(f"{env} -> {reason}")
