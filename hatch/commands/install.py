import os
import subprocess
import sys

import click

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting
)
from hatch.config import get_proper_pip, get_venv_dir
from hatch.env import install_packages
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, ON_WINDOWS, get_admin_command, is_project, venv_active
)
from hatch.venv import create_venv, is_venv, venv


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Installs packages')
@click.argument('packages', nargs=-1)
@click.option('-nd', '--no-detect', is_flag=True,
              help=(
                  "Disables the use of a project's dedicated virtual env. "
                  'This is useful if you need to be in a project root but '
                  'wish to not target its virtual env.'
              ))
@click.option('-e', '--env', 'env_name', help='The named virtual env to use.')
@click.option('-l', '--local', 'editable', is_flag=True,
              help=(
                  "Corresponds to pip's --editable option, allowing a local "
                  "package to be automatically updated when modifications "
                  "are made."
              ))
@click.option('-g', '--global', 'global_install', is_flag=True,
              help=(
                  'Installs globally, rather than on a per-user basis. This '
                  'has no effect if a virtual env is in use.'
              ))
@click.option('--admin', is_flag=True,
              help=(
                  'When --global is selected, this assumes admin rights are '
                  'already enabled and therefore sudo/runas will not be used.'
              ))
@click.option('-q', '--quiet', is_flag=True, help='Decreases verbosity.')
def install(packages, no_detect, env_name, editable, global_install, admin, quiet):
    """If the option --env is supplied, the install will be applied using
    that named virtual env. Unless the option --global is selected, the
    install will only affect the current user. Of course, this will have
    no effect if a virtual env is in use. The desired name of the admin
    user can be set with the `_DEFAULT_ADMIN_` environment variable.

    With no packages selected, this will install using a `setup.py` in the
    current directory.

    If no --env is chosen, this will attempt to detect a project and use its
    virtual env before resorting to the default pip. No project detection
    will occur if a virtual env is active.
    """
    packages = packages or ['.']

    # Windows' `runas` allows only a single argument for the
    # command so we catch this case and turn our command into
    # a string later.
    windows_admin_command = None

    if editable:
        packages = ['-e', *packages]

    if env_name:
        venv_dir = os.path.join(get_venv_dir(), env_name)
        if not os.path.exists(venv_dir):
            echo_failure('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            command = [get_proper_pip(), 'install', *packages] + (['-q'] if quiet else [])
            echo_waiting('Installing in virtual env `{}`...'.format(env_name))
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    elif not venv_active() and not no_detect and is_project():
        venv_dir = os.path.join(os.getcwd(), 'venv')
        if not is_venv(venv_dir):
            echo_info('A project has been detected!')
            echo_waiting('Creating a dedicated virtual env... ', nl=False)
            create_venv(venv_dir)
            echo_success('complete!')

            with venv(venv_dir):
                echo_waiting('Installing this project in the virtual env... ', nl=False)
                install_packages(['-q', '-e', '.'])
                echo_success('complete!')

        with venv(venv_dir):
            command = [get_proper_pip(), 'install', *packages] + (['-q'] if quiet else [])
            echo_waiting('Installing for this project...')
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    else:
        command = [get_proper_pip(), 'install'] + (['-q'] if quiet else [])

        if not venv_active():  # no cov
            if global_install:
                if not admin:
                    if ON_WINDOWS:
                        windows_admin_command = get_admin_command()
                    else:
                        command = get_admin_command() + command
            else:
                command.append('--user')

        command.extend(packages)

        if windows_admin_command:  # no cov
            command = windows_admin_command + [' '.join(command)]

        echo_waiting('Installing...')
        result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)

    sys.exit(result.returncode)
