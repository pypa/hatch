"""Top-level ``hatch lock`` — forwards to the same workflow as ``hatch dep lock``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from hatch.cli.env.lock import dependency_lock_click_options, run_dep_lock

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(
    name="lock",
    short_help="Generate a lockfile for the active environment (alias for `hatch dep lock`)",
)
@dependency_lock_click_options
@click.pass_obj
def lock_command(
    app: Application,
    *,
    upgrade: bool,
    upgrade_package: tuple[str, ...],
    export_path: str | None,
    export_all_path: str | None,
    check: bool,
):
    """Same as :command:`hatch dep lock` for the environment selected with ``-e`` / ``HATCH_ENV``."""
    app.ensure_environment_plugin_dependencies()
    run_dep_lock(
        app,
        upgrade=upgrade,
        upgrade_package=upgrade_package,
        export_path=export_path,
        export_all_path=export_all_path,
        check=check,
    )
