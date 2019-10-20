import os
import subprocess
import sys

import click
import userpath

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting,
    echo_warning
)
from hatch.conda import get_conda_new_exe_path
from hatch.exceptions import InvalidVirtualEnv
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, ON_MACOS, ON_WINDOWS, conda_available,
    download_file, is_os_64bit, temp_chdir
)
from hatch.venv import locate_exe_dir


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Installs Miniconda')
@click.argument('location')
@click.option('-f', '--force', is_flag=True,
              help='Proceed through errors and even if Conda is already installed.')
@click.option('--head/--tail',
              help='Adds Conda to the head or tail (default) of the user PATH.')
@click.option('--install-only', is_flag=True, help='Does not modify the user PATH.')
@click.option('--show', is_flag=True,
              help='Does nothing but show what would be added to the user PATH.')
def conda(location, force, head, install_only, show):  # no cov
    """Installs Miniconda https://conda.io/docs/glossary.html#miniconda-glossary"""
    location = userpath.utils.normpath(location)
    new_path = get_conda_new_exe_path(location)

    if show:
        echo_info(new_path)
        return

    if os.path.exists(location) and not force:
        echo_warning((
            '`{}` already exists! If you are sure you want to proceed, '
            'try again with the -f/--force flag.'.format(location)
        ))
        sys.exit(2)

    if not install_only and not force and conda_available():
        echo_warning((
            'Conda is already in PATH! If you are sure you want '
            'to proceed, try again with the -f/--force flag.'
        ))
        sys.exit(2)
    else:
        if ON_WINDOWS:
            installer_name = 'installer.exe'
            if is_os_64bit():
                url = 'https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe'
            else:
                url = 'https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86.exe'
        else:
            installer_name = 'installer.sh'
            if ON_MACOS:
                if is_os_64bit():
                    url = 'https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh'
                else:
                    echo_failure('Conda is not available for 32-bit macOS, sorry!')
                    sys.exit(1)
            else:
                if is_os_64bit():
                    url = 'https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh'
                else:
                    url = 'https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86.sh'

        with temp_chdir() as d:
            fname = os.path.join(d, installer_name)
            echo_waiting('Downloading installer to a temporary directory... ', nl=False)
            download_file(url, fname)
            echo_success('complete!')

            if ON_WINDOWS:
                command = [
                    'start', '/wait', '', fname, '/S', '/InstallationType=JustMe',
                    '/AddToPath=0', '/RegisterPython=0', '/D={}'.format(location)
                ]
            else:
                command = ['bash', fname, '-b', '-p', location]

            try:
                echo_waiting('Installing, please wait...')
                subprocess.run(command, shell=NEED_SUBPROCESS_SHELL, check=True)
            except subprocess.CalledProcessError:
                echo_failure('Installation has seemingly failed! ', nl=False)
                if force:
                    echo_warning('Proceeding by force...')
                else:
                    echo_failure('Exiting...')
                    sys.exit(1)

    try:
        locate_exe_dir(location)
    except InvalidVirtualEnv:
        echo_failure('Installation has definitely failed! Exiting...')
        sys.exit(1)

    echo_success('Successfully installed Conda!')

    if not install_only:
        add_to_path = userpath.prepend if head else userpath.append
        success = add_to_path(new_path, app_name='Hatch')

        if success:
            echo_info(
                'Please restart your shell for PATH changes to take effect.'
            )
        else:
            echo_warning(
                'It appears that we were unable to modify PATH. Please '
                'do so using the following: ', nl=False
            )
            echo_info(new_path)
