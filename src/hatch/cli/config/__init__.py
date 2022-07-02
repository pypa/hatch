import os

import click


@click.group(short_help='Manage the config file')
def config():
    pass


@config.command(short_help='Open the config location in your file manager')
@click.pass_obj
def explore(app):
    """Open the config location in your file manager."""
    click.launch(str(app.config_file.path), locate=True)


@config.command(short_help='Show the location of the config file')
@click.option('--copy', '-c', is_flag=True, help='Copy the path to the config file to the clipboard')
@click.pass_obj
def find(app, copy):
    """Show the location of the config file."""
    config_path = str(app.config_file.path)
    if copy:
        import pyperclip

        pyperclip.copy(config_path)
    elif ' ' in config_path:
        app.display_info(f'"{config_path}"')
    else:
        app.display_info(config_path)


@config.command(short_help='Show the contents of the config file')
@click.option('--all', '-a', 'all_keys', is_flag=True, help='Do not scrub secret fields')
@click.pass_obj
def show(app, all_keys):
    """Show the contents of the config file."""
    if not app.config_file.path.is_file():  # no cov
        app.display_info('No config file found! Please try `hatch config restore`.')
    else:
        from rich.syntax import Syntax

        text = app.config_file.read() if all_keys else app.config_file.read_scrubbed()
        app.display(Syntax(text.rstrip(), 'toml', background_color='default'))


@config.command(short_help='Update the config file with any new fields')
@click.pass_obj
def update(app):  # no cov
    """Update the config file with any new fields."""
    app.config_file.update()
    app.display_success('Settings were successfully updated.')


@config.command(short_help='Restore the config file to default settings')
@click.pass_obj
def restore(app):
    """Restore the config file to default settings."""
    app.config_file.restore()
    app.display_success('Settings were successfully restored.')


@config.command('set', short_help='Assign values to config file entries')
@click.argument('key')
@click.argument('value', required=False)
@click.pass_obj
def set_value(app, key, value):
    """
    Assign values to config file entries. If the value is omitted,
    you will be prompted, with the input hidden if it is sensitive.
    """
    from fnmatch import fnmatch

    import tomlkit

    from hatch.config.model import ConfigurationError, RootConfig
    from hatch.config.utils import create_toml_document, save_toml_document

    scrubbing = key.startswith('publish.')
    if value is None:
        value = click.prompt(f'Value for `{key}`', hide_input=scrubbing)

    setting_project_location = bool(fnmatch(key, 'projects.*') or fnmatch(key, 'projects.*.location'))
    if setting_project_location and not value.startswith('~'):
        value = os.path.abspath(value)

    user_config = new_config = tomlkit.parse(app.config_file.read())

    data = [value]
    data.extend(reversed(key.split('.')))
    key = data.pop()
    value = data.pop()

    # Use a separate mapping to show only what has changed in the end
    branch_config_root = branch_config = {}

    # Consider dots as keys
    while data:
        default_branch = {value: ''}
        branch_config[key] = default_branch
        branch_config = branch_config[key]

        new_value = new_config.get(key)
        if not hasattr(new_value, 'get'):
            new_value = default_branch

        new_config[key] = new_value
        new_config = new_config[key]

        key = value
        value = data.pop()

    if value.startswith(('{', '[')):
        from ast import literal_eval

        value = literal_eval(value)

    branch_config[key] = new_config[key] = value

    # https://github.com/sdispater/tomlkit/issues/48
    if new_config.__class__.__name__ == 'Table':  # no cov
        table_body = getattr(new_config.value, 'body', [])
        possible_whitespace = table_body[-2:]
        if len(possible_whitespace) == 2:
            for key, item in possible_whitespace:
                if key is not None:
                    break
                if item.__class__.__name__ != 'Whitespace':
                    break
            else:
                del table_body[-2]

    try:
        RootConfig(user_config).parse_fields()
    except ConfigurationError as e:
        app.display_error(str(e))
        app.abort()
    else:
        if not user_config['project'] and setting_project_location:
            project = list(branch_config_root['projects'])[0]
            user_config['project'] = project
            branch_config_root['project'] = project

        save_toml_document(user_config, app.config_file.path)

    document = create_toml_document(branch_config_root)
    if scrubbing and 'publish' in document:
        for data in document['publish'].values():
            for field in list(data):
                data[field] = '<...>'

    from rich.syntax import Syntax

    app.display_success('New setting:')
    app.display(Syntax(tomlkit.dumps(document).rstrip(), 'toml', background_color='default'))
