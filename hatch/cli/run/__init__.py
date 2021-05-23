import click


@click.command(
    short_help="Run a command within a project's environment",
    context_settings={'help_option_names': [], 'ignore_unknown_options': True},
)
@click.argument('args', required=True, nargs=-1)
@click.pass_obj
def run(app, args):
    """Run commands within a project's environment."""
    project = app.project

    command, *args = args
    env_name, separator, command = command.rpartition(':')
    if not separator:
        env_name = app.env

    args = [command, *args]

    system_environment = False
    if not env_name:
        system_environment = True
        env_name = 'system'
        project.config.config['envs'] = {
            env_name: {
                'type': env_name,
                'skip-install': True,
                'scripts': project.config.scripts,
            }
        }

    is_matrix = False
    if env_name in project.config.matrices:
        is_matrix = True
        environments = project.config.matrices[env_name]
    else:
        environments = [env_name]

    any_compatible = False
    incompatible = {}
    with project.location.as_cwd():
        for env_name in environments:
            environment = app.get_environment(env_name)

            try:
                environment.check_compatibility()
            except Exception as e:
                if is_matrix:
                    incompatible[environment.name] = str(e)
                    continue
                else:
                    app.abort(f'Environment `{env_name}` is incompatible: {e}')

            any_compatible = True
            if is_matrix:
                app.display_header(environment.name)

            if system_environment:
                environment.exists = lambda: True

            app.prepare_environment(environment)

            for process in environment.run_shell_commands([environment.join_command_args(args)]):
                if process.returncode:
                    app.abort(code=process.returncode)

    if incompatible:
        num_incompatible = len(incompatible)
        padding = '\n' if any_compatible else ''
        app.display_warning(
            f'{padding}Skipped {num_incompatible} incompatible environment{"s" if num_incompatible > 1 else ""}:'
        )
        for env_name, reason in incompatible.items():
            app.display_warning(f'{env_name} -> {reason}')
