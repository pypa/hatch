import click

from hatch.commands.utils import CONTEXT_SETTINGS, echo_success
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, load_settings, restore_settings,
    save_settings
)


@click.command(context_settings=CONTEXT_SETTINGS,
               short_help='Locates, updates, or restores the config file')
@click.option('-u', '--update', 'update_settings', is_flag=True,
              help='Updates the config file with any new fields.')
@click.option('--restore', is_flag=True,
              help='Restores the config file to default settings.')
def config(update_settings, restore):
    """Locates, updates, or restores the config file.

    \b
    $ hatch config
    Settings location: /home/ofek/.local/share/hatch/settings.json
    """
    if update_settings:
        try:
            user_settings = load_settings()
            updated_settings = copy_default_settings()
            updated_settings.update(user_settings)
            save_settings(updated_settings)
            echo_success('Settings were successfully updated.')
        except FileNotFoundError:
            restore = True

    if restore:
        restore_settings()
        echo_success('Settings were successfully restored.')

    echo_success('Settings location: ' + SETTINGS_FILE)
