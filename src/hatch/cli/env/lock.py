from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


def dependency_lock_click_options(fn):
    """Options shared by ``hatch dep lock`` and top-level ``hatch lock``."""
    decorators = [
        click.option("--upgrade", "-U", is_flag=True, help="Upgrade all packages"),
        click.option("--upgrade-package", "-P", multiple=True, help="Upgrade specific package(s)"),
        click.option(
            "--export", "export_path", type=click.Path(), default=None, help="Export lockfile to a custom path"
        ),
        click.option(
            "--export-all",
            "export_all_path",
            type=click.Path(),
            default=None,
            help="Export lockfiles for all environments to a directory",
        ),
        click.option("--check", is_flag=True, help="Check if lockfile is up-to-date"),
    ]
    for d in reversed(decorators):
        fn = d(fn)
    return fn


def run_dep_lock(
    app: Application,
    *,
    upgrade: bool,
    upgrade_package: tuple[str, ...],
    export_path: str | None,
    export_all_path: str | None,
    check: bool,
) -> None:
    """Lock workflow for the active ``HATCH_ENV`` (``hatch -e``), with ``--export-all`` matching ``hatch env lock``."""
    if export_path and export_all_path:
        app.abort("Cannot use both `--export` and `--export-all`")

    if export_all_path:
        env_names = [*app.project.config.envs, *app.project.config.internal_envs]
        explicit_env = None
        skip_incompatible = True
    else:
        env_names = app.project.expand_environments(app.env)
        if not env_names:
            app.abort(f"Environment `{app.env}` is not defined by project config")
        explicit_env = app.env
        skip_incompatible = app.env in app.project.config.matrices

    run_lock_workflow(
        app,
        env_names,
        upgrade=upgrade,
        upgrade_package=upgrade_package,
        export_path=export_path,
        export_all_path=export_all_path,
        check=check,
        explicit_env=explicit_env,
        skip_incompatible_envs=skip_incompatible,
    )


def run_lock_workflow(
    app: Application,
    env_names: list[str],
    *,
    upgrade: bool,
    upgrade_package: tuple[str, ...],
    export_path: str | None,
    export_all_path: str | None,
    check: bool,
    explicit_env: str | None,
    skip_incompatible_envs: bool,
) -> None:
    """Shared implementation for ``hatch env lock`` and ``hatch dep lock``."""
    from hatch.env.lock import (
        LockerNotFoundError,
        LockerUnsupportedError,
        environment_has_lock_inputs,
        generate_lockfile,
        lockfile_in_sync,
        merge_environment_lock_inputs,
        resolve_lockfile_path,
    )
    from hatch.utils.fs import Path

    incompatible: dict[str, str] = {}
    lockfile_groups: dict[Path, list[str]] = {}

    for env in env_names:
        environment = app.project.get_environment(env)

        try:
            environment.check_compatibility()
        except Exception as e:  # noqa: BLE001
            if skip_incompatible_envs:
                incompatible[env] = str(e)
                continue

            app.abort(f"Environment `{env}` is incompatible: {e}")

        if explicit_env is not None and not environment.locked and not export_path and not export_all_path:
            app.abort(
                f"Environment `{explicit_env}` is not configured with `locked = true`. "
                f"Use `--export <path>` to generate a lockfile, "
                f"or set `locked = true` on the environment (or `lock-envs = true` globally)."
            )

        if export_path:
            output_path = Path(export_path)
        elif export_all_path:
            safe_name = environment.name.replace(".", "-")
            filename = "pylock.toml" if environment.name == "default" else f"pylock.{safe_name}.toml"
            output_path = Path(export_all_path) / filename
        else:
            output_path = resolve_lockfile_path(environment)

        if check:
            if not output_path.is_file():
                app.abort(f"Lockfile does not exist: {output_path}")
        elif not environment_has_lock_inputs(environment):
            app.display_warning(f"Environment `{env}` has no dependencies to lock")
            continue

        lockfile_groups.setdefault(output_path, []).append(env)

    for output_path, envs in lockfile_groups.items():
        environment, merged_deps, merged_extras, merged_groups, display_name = merge_environment_lock_inputs(
            app.project, envs, app.abort
        )

        try:
            if check:
                with app.status(f"Checking lockfile for: {display_name}"):
                    if not lockfile_in_sync(
                        environment,
                        output_path,
                        upgrade=upgrade,
                        upgrade_packages=upgrade_package,
                        deps_override=merged_deps,
                        lock_extras=merged_extras,
                        lock_groups=merged_groups,
                    ):
                        app.abort(f"Lockfile is not up to date: {output_path}")
                app.display(f"Lockfile is up to date: {output_path}")
                continue

            with app.status(f"Locking environment: {display_name}"):
                generate_lockfile(
                    environment,
                    output_path,
                    upgrade=upgrade,
                    upgrade_packages=upgrade_package,
                    deps_override=merged_deps,
                    lock_extras=merged_extras,
                    lock_groups=merged_groups,
                )

            app.display(f"Wrote lockfile: {output_path}")
        except LockerNotFoundError as e:
            app.abort(str(e))
        except LockerUnsupportedError as e:
            app.abort(str(e))

    if incompatible:
        num_incompatible = len(incompatible)
        app.display_warning(
            f"Skipped {num_incompatible} incompatible environment{'s' if num_incompatible > 1 else ''}:"
        )
        for env, reason in incompatible.items():
            app.display_warning(f"{env} -> {reason}")


@click.command(short_help="Generate lockfiles for environments")
@click.argument("env_name", required=False, default=None)
@click.option("--upgrade", "-U", is_flag=True, help="Upgrade all packages")
@click.option("--upgrade-package", "-P", multiple=True, help="Upgrade specific package(s)")
@click.option("--export", "export_path", type=click.Path(), default=None, help="Export lockfile to a custom path")
@click.option(
    "--export-all",
    "export_all_path",
    type=click.Path(),
    default=None,
    help="Export lockfiles for all environments to a directory",
)
@click.option("--check", is_flag=True, help="Check if lockfile is up-to-date")
@click.pass_obj
def lock(
    app: Application,
    *,
    env_name: str | None,
    upgrade: bool,
    upgrade_package: tuple[str, ...],
    export_path: str | None,
    export_all_path: str | None,
    check: bool,
):
    """Generate lockfiles for environments.

    When called without arguments, locks all environments that have `locked = true`
    in their configuration. When called with ENV_NAME, locks that specific environment.
    """
    app.ensure_environment_plugin_dependencies()

    if export_path and export_all_path:
        app.abort("Cannot use both `--export` and `--export-all`")

    if export_all_path:
        env_names = [*app.project.config.envs, *app.project.config.internal_envs]
        explicit_env = None
        skip_incompatible = True
    elif env_name is not None:
        env_names = app.project.expand_environments(env_name)
        if not env_names:
            app.abort(f"Environment `{env_name}` is not defined by project config")
        explicit_env = env_name
        skip_incompatible = env_name in app.project.config.matrices
    else:
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
        explicit_env = None
        skip_incompatible = True

    run_lock_workflow(
        app,
        env_names,
        upgrade=upgrade,
        upgrade_package=upgrade_package,
        export_path=export_path,
        export_all_path=export_all_path,
        check=check,
        explicit_env=explicit_env,
        skip_incompatible_envs=skip_incompatible,
    )
