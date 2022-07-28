import click


@click.command(short_help="Enter a shell within a project's environment")
@click.argument('shell_name', required=False)
@click.argument('shell_path', required=False)
@click.argument('shell_args', required=False, nargs=-1)
@click.pass_obj
def shell(app, shell_name, shell_path, shell_args):  # no cov
    """Enter a shell within a project's environment."""
    if app.env == app.env_active:
        app.abort(f'Already in environment: {app.env}')

    if app.env in app.project.config.matrices:
        app.display_error(f'Environment `{app.env}` defines a matrix, choose one of the following instead:\n')
        for env_name in app.project.config.matrices[app.env]['envs']:
            app.display_error(env_name)

        app.abort()

    if not shell_name:
        shell_name = app.config.shell.name
    if not shell_path:
        shell_path = app.config.shell.path
    if not shell_args:
        shell_args = app.config.shell.args

    if not shell_path:
        import shellingham

        try:
            shell_name, command = shellingham.detect_shell()
        except shellingham.ShellDetectionFailure:
            from hatch.utils.fs import Path

            shell_path = app.platform.default_shell
            shell_name = Path(shell_path).stem
        else:
            if app.platform.windows:
                shell_path = command
            else:
                shell_path, *shell_args = app.platform.modules.shlex.split(command)

    with app.project.location.as_cwd():
        environment = app.get_environment()
        app.prepare_environment(environment)

        first_run_indicator = app.cache_dir / 'shell' / 'first_run'
        if not first_run_indicator.is_file():
            app.display_waiting(
                'You are about to enter a new shell, exit as you usually would e.g. '
                'by typing `exit` or pressing `ctrl+d`...'
            )
            first_run_indicator.parent.ensure_dir_exists()
            first_run_indicator.touch()

        environment.enter_shell(shell_name, shell_path, shell_args)
