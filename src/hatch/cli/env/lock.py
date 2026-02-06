from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help="Generate lockfiles for environments")
@click.argument("env_name", default="default")
@click.option("--all", "lock_all", is_flag=True, help="Lock all environments")
@click.option("--upgrade", "-U", is_flag=True, help="Upgrade all packages")
@click.option("--upgrade-package", "-P", multiple=True, help="Upgrade specific package(s)")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file path")
@click.option("--check", is_flag=True, help="Check if lockfile is up-to-date")
@click.pass_obj
def lock(
    app: Application,
    env_name: str,
    *,
    lock_all: bool,
    upgrade: bool,
    upgrade_package: tuple[str, ...],
    output: str | None,
    check: bool,
):
    """Generate lockfiles for environments."""
    app.ensure_environment_plugin_dependencies()

    if lock_all:
        env_names = list(app.project.config.envs)
    else:
        env_names = app.project.expand_environments(env_name)
        if not env_names:
            app.abort(f"Environment `{env_name}` is not defined by project config")

    from hatch.env.lock import generate_lockfile, resolve_output_path

    incompatible = {}
    for env in env_names:
        environment = app.project.get_environment(env)

        try:
            environment.check_compatibility()
        except Exception as e:  # noqa: BLE001
            if env_name in app.project.config.matrices:
                incompatible[env] = str(e)
                continue

            app.abort(f"Environment `{env}` is incompatible: {e}")

        output_path = resolve_output_path(environment, output)

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
