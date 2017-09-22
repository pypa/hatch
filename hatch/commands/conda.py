import os
import subprocess
import sys

import click
import userpath

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_success, echo_warning
)
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, ON_MACOS, ON_WINDOWS, conda_available,
    download_file, is_os_64bit, remove_path, temp_chdir
)


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Installs Miniconda')
@click.argument('location')
@click.option('-f', '--force', is_flag=True, help='Reinstall')
def conda(location, force):  # no cov
    if not force and conda_available():
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
            download_file(url, fname)

            location = os.path.abspath(location)
            if os.path.exists(location):
                if force:
                    remove_path(location)
                else:
                    echo_warning((
                        '`{}` already exists! If you are sure you want to proceed, '
                        'try again with the -f/--force flag.'.format(location)
                    ))
                    sys.exit(2)

            if ON_WINDOWS:
                command = [
                    'start', '/wait', '', fname, '/S', '/InstallationType=JustMe',
                    '/AddToPath=0', '/RegisterPython=0', '/D={}'.format(location)
                ]
            else:
                command = ['bash', fname, '-b', '-p', location]

            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)














