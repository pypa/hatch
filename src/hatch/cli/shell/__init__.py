import click


@click.command(short_help="Enter a shell within a project's environment")
@click.argument('shell_name', required=False)
@click.argument('shell_path', required=False)
@click.pass_obj
def shell(app, shell_name, shell_path):  # no cov
    """Enter a shell within a project's environment."""
    if app.env == app.env_active:
        app.abort(f'Already in environment: {app.env}')

    if app.env in app.project.config.matrices:
        app.display_error(f'Environment `{app.env}` defines a matrix, choose one of the following instead:\n')
        for env_name in app.project.config.matrices[app.env]:
            app.display_error(env_name)

        app.abort()

    if not shell_name:
        shell_name = app.config.shell.name
    if not shell_path:
        shell_path = app.config.shell.path

    if not shell_path:
        from ...utils.fs import Path

        shell_path = app.platform.default_shell
        shell_name = Path(shell_path).stem

    with app.project.location.as_cwd():
        environment = app.get_environment()
        app.prepare_environment(environment)

        environment.enter_shell(shell_name, shell_path)
