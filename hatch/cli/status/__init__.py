import click


@click.command(short_help='Show information about the current environment')
@click.pass_obj
def status(app):
    """Show information about the current environment."""

    def display_pair(key, value, display_func=None, link=None):
        app.display_info('[', end='')
        app.display_success(key, end='')
        app.display_info(']', end='')
        app.display_info(' - ', end='')
        (display_func or app.display_info)(value, link=link)

    if app.project.root is None:
        if app.project.chosen_name is None:
            display_pair('Project', '<no project detected>', app.display_warning)
        else:
            display_pair('Project', f'{app.project.chosen_name} (not a project)', app.display_warning)
    else:
        if app.project.chosen_name is None:
            display_pair('Project', f'{app.project.root.name} (current directory)')
        else:
            display_pair('Project', app.project.chosen_name)

    display_pair('Location', str(app.project.location))
    display_pair('Config', str(app.config_file.path), link=f'file:///{app.config_file.path}')
