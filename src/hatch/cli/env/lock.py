from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


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

    from hatch.env.lock import generate_lockfile, resolve_lockfile_path
    from hatch.utils.fs import Path

    if export_path and export_all_path:
        app.abort("Cannot use both `--export` and `--export-all`")

    if export_all_path:
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

    # Resolve environments, check compatibility, and determine output paths
    incompatible = {}
    lockfile_groups: dict[Path, list[str]] = {}

    for env in env_names:
        environment = app.project.get_environment(env)

        try:
            environment.check_compatibility()
        except Exception as e:  # noqa: BLE001
            if env_name is None or env_name in app.project.config.matrices:
                incompatible[env] = str(e)
                continue

            app.abort(f"Environment `{env}` is incompatible: {e}")

        # Require --export for non-locked environments when explicitly named
        if env_name is not None and not environment.locked and not export_path and not export_all_path:
            app.abort(
                f"Environment `{env_name}` is not configured with `locked = true`. "
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
            app.display(f"Lockfile exists: {output_path}")
            continue

        if not environment.dependencies:
            app.display_warning(f"Environment `{env}` has no dependencies to lock")
            continue

        lockfile_groups.setdefault(output_path, []).append(env)

    # Generate lockfiles, deduplicating when multiple envs share a path
    for output_path, envs in lockfile_groups.items():
        # Merge dependencies from all environments sharing this lockfile
        if len(envs) == 1:
            environment = app.project.get_environment(envs[0])
            merged_deps = None
            display_name = envs[0]
        else:
            seen: set[str] = set()
            merged: list[str] = []
            python_versions: set[str] = set()
            for env in envs:
                env_obj = app.project.get_environment(env)
                for dep in env_obj.dependencies:
                    if dep not in seen:
                        seen.add(dep)
                        merged.append(dep)
                python_version = env_obj.config.get("python", "")
                python_versions.add(python_version)

            if len(python_versions) > 1:
                versions_str = ", ".join(sorted(v for v in python_versions if v) or ["(default)"])
                app.abort(
                    f"Environments sharing lockfile `{output_path.name}` target different Python versions "
                    f"({versions_str}). A single lockfile cannot be valid across different Python versions. "
                    f"Use distinct `lock-filename` values for each Python version."
                )

            merged_deps = merged
            environment = app.project.get_environment(envs[0])
            display_name = ", ".join(envs)

        with app.status(f"Locking environment: {display_name}"):
            generate_lockfile(
                environment,
                output_path,
                upgrade=upgrade,
                upgrade_packages=upgrade_package,
                deps_override=merged_deps,
            )

        app.display(f"Wrote lockfile: {output_path}")

    if incompatible:
        num_incompatible = len(incompatible)
        app.display_warning(
            f"Skipped {num_incompatible} incompatible environment{'s' if num_incompatible > 1 else ''}:"
        )
        for env, reason in incompatible.items():
            app.display_warning(f"{env} -> {reason}")
