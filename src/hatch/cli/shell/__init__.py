from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help="Enter a shell within a project's environment")
@click.argument('env_name', required=False)
@click.option('--name')
@click.option('--path')
@click.pass_obj
def shell(app: Application, env_name: str | None, name: str, path: str):  # no cov
    """Enter a shell within a project's environment."""
    app.ensure_environment_plugin_dependencies()

    chosen_env = env_name or app.env
    if chosen_env == app.env_active:
        app.abort(f'Already in environment: {chosen_env}')

    for matrices in (app.project.config.matrices, app.project.config.internal_matrices):
        if chosen_env in matrices:
            app.display_error(f'Environment `{chosen_env}` defines a matrix, choose one of the following instead:\n')
            for generated_name in matrices[chosen_env]['envs']:
                app.display_error(generated_name)

            app.abort()

    if not name:
        name = app.config.shell.name
    if not path:
        path = app.config.shell.path

    args = app.config.shell.args
    if not path:
        name, path = app.shell_data
        if not app.platform.windows:
            path, *args = app.platform.modules.shlex.split(path)

    with app.project.ensure_cwd():
        environment = app.get_environment(chosen_env)
        app.prepare_environment(environment)

        first_run_indicator = app.cache_dir / 'shell' / 'first_run'
        if not first_run_indicator.is_file():
            app.display_waiting(
                'You are about to enter a new shell, exit as you usually would e.g. '
                'by typing `exit` or pressing `ctrl+d`...'
            )
            first_run_indicator.parent.ensure_dir_exists()
            first_run_indicator.touch()

        environment.enter_shell(name, path, args)
