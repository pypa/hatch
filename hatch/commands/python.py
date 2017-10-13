import os
import shutil
import subprocess
import sys

import click
import userpath

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting,
    echo_warning
)
from hatch.conda import get_conda_new_exe_path
from hatch.config import get_python_dir
from hatch.settings import copy_default_settings, load_settings, save_settings
from hatch.utils import ON_WINDOWS, conda_available, resolve_path


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Manages Python installations')
@click.argument('version')
@click.argument('name', required=False)
@click.option('--head/--tail', is_flag=True, default=None,
              help='Adds the installation to the head or tail of the user PATH.')
def python(version, name, head):  # no cov
    if not conda_available():
        echo_failure('Conda is unavailable. You can install it by doing `hatch conda`.')
        sys.exit(1)

    exe_name = 'py{}'.format(name or version) + ('.exe' if ON_WINDOWS else '')
    name = name or version
    path = os.path.join(get_python_dir(), name)
    command = ['conda', 'create', '--yes', '-p', path, 'python={}'.format(version)]

    if os.path.exists(path):
        echo_failure('The path `{}` already exists.'.format(path))
        sys.exit(1)

    settings = load_settings(lazy=True)
    if 'pypaths' not in settings:
        updated_settings = copy_default_settings()
        updated_settings.update(settings)
        settings = updated_settings
        echo_success('Settings were successfully updated to include `pypaths` entry.')

    old_path = settings['pypaths'].get(name)
    if old_path:
        echo_failure('The Python path `{}` already points to `{}`.'.format(name, old_path))
        sys.exit(1)

    echo_waiting('Installing Python {}...'.format(version))
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        echo_failure('The installation was seemingly unsuccessful.')
        click.echo(e.stdout)
        click.echo(e.stderr)
        sys.exit(e.returncode)

    conda_path = get_conda_new_exe_path(path)
    python_path = resolve_path(shutil.which('python', path=conda_path))
    settings['pypaths'][name] = python_path
    save_settings(settings)
    echo_success('Successfully saved Python `{}` located at `{}`.'.format(name, python_path))

    if head is not None:
        add_to_path = userpath.prepend if head else userpath.append
        success = add_to_path(conda_path, app_name='Hatch')
        shutil.copy(python_path, os.path.join(os.path.dirname(python_path), exe_name))

        if success:
            echo_info(
                'Please restart your shell for PATH changes to take effect.'
            )
        else:
            echo_warning(
                'It appears that we were unable to modify PATH. Please '
                'do so using the following: ', nl=False
            )
            echo_info(conda_path)
