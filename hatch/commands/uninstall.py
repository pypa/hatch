import os
import subprocess
import sys

import click

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting,
    echo_warning
)
from hatch.config import get_proper_pip, get_venv_dir
from hatch.env import install_packages
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, ON_WINDOWS, get_admin_command, get_requirements_file,
    is_project, venv_active
)
from hatch.venv import create_venv, is_venv, venv


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Uninstalls packages')
@click.argument('packages', nargs=-1)
@click.option('-nd', '--no-detect', is_flag=True,
              help=(
                  "Disables the use of a project's dedicated virtual env. "
                  'This is useful if you need to be in a project root but '
                  'wish to not target its virtual env.'
              ))
@click.option('-e', '--env', 'env_name', help='The named virtual env to use.')
@click.option('-g', '--global', 'global_uninstall', is_flag=True,
              help=(
                  'Uninstalls globally, rather than on a per-user basis. This '
                  'has no effect if a virtual env is in use.'
              ))
@click.option('--admin', is_flag=True,
              help=(
                  'When --global is selected, this assumes admin rights are '
                  'already enabled and therefore sudo/runas will not be used.'
              ))
@click.option('-d', '--dev', is_flag=True,
              help='When locating a requirements file, only use the dev version.')
@click.option('-q', '--quiet', is_flag=True, help='Decreases verbosity.')
@click.option('-y', '--yes', is_flag=True,
              help='Confirms the intent to uninstall without a prompt.')
def uninstall(packages, no_detect, env_name, global_uninstall, admin, dev, quiet, yes):
    """If the option --env is supplied, the uninstall will be applied using
    that named virtual env. Unless the option --global is selected, the
    uninstall will only affect the current user. Of course, this will have
    no effect if a virtual env is in use. The desired name of the admin
    user can be set with the `_DEFAULT_ADMIN_` environment variable.

    With no packages selected, this will uninstall using a `requirements.txt`
    or a dev version of that in the current directory.

    If no --env is chosen, this will attempt to detect a project and use its
    virtual env before resorting to the default pip. No project detection
    will occur if a virtual env is active.
    """
    if not packages:
        reqs = get_requirements_file(os.getcwd(), dev=dev)
        if not reqs:
            echo_failure('Unable to locate a requirements file.')
            sys.exit(1)

        packages = ['-r', reqs]

    # Windows' `runas` allows only a single argument for the
    # command so we catch this case and turn our command into
    # a string later.
    windows_admin_command = None

    if yes:  # no cov
        packages = ['-y', *packages]

    if env_name:
        venv_dir = os.path.join(get_venv_dir(), env_name)
        if not os.path.exists(venv_dir):
            echo_failure('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            command = [get_proper_pip(), 'uninstall', *packages] + (['-q'] if quiet else [])
            echo_waiting('Uninstalling in virtual env `{}`...'.format(env_name))
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

            echo_warning('New virtual envs have nothing to uninstall, exiting...')
            sys.exit(2)

        with venv(venv_dir):
            command = [get_proper_pip(), 'uninstall', *packages] + (['-q'] if quiet else [])
            echo_waiting('Uninstalling for this project...')
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    else:
        command = [get_proper_pip(), 'uninstall'] + (['-q'] if quiet else [])

        if not venv_active() and global_uninstall:  # no cov
            if not admin:
                if ON_WINDOWS:
                    windows_admin_command = get_admin_command()
                else:
                    command = get_admin_command() + command

        command.extend(packages)

        if windows_admin_command:  # no cov
            command = windows_admin_command + [' '.join(command)]

        echo_waiting('Uninstalling...')
        result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)

    sys.exit(result.returncode)
