import os
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

import click

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting,
    echo_warning
)
from hatch.config import get_proper_pip, get_proper_python, get_venv_dir
from hatch.env import get_installed_packages, install_packages
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, ON_WINDOWS, basepath, get_admin_command,
    get_requirements_file, is_project, venv_active
)
from hatch.venv import create_venv, is_venv, venv


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Updates packages')
@click.argument('packages', nargs=-1)
@click.option('-nd', '--no-detect', is_flag=True,
              help=(
                  "Disables the use of a project's dedicated virtual env. "
                  'This is useful if you need to be in a project root but '
                  'wish to not target its virtual env.'
              ))
@click.option('-e', '--env', 'env_name', help='The named virtual env to use.')
@click.option('--eager', is_flag=True,
              help=(
                  'Updates all dependencies regardless of whether they '
                  'still satisfy the new parent requirements. See: '
                  'https://github.com/pypa/pip/pull/3972'
              ))
@click.option('--all', 'all_packages', is_flag=True,
              help=(
                  'Updates all currently installed packages. The packages '
                  '`pip`, `setuptools`, and `wheel` are excluded.'
              ))
@click.option('--infra', is_flag=True,
              help='Updates only the packages `pip`, `setuptools`, and `wheel`.')
@click.option('-g', '--global', 'global_install', is_flag=True,
              help=(
                  'Updates globally, rather than on a per-user basis. This '
                  'has no effect if a virtual env is in use.'
              ))
@click.option('--admin', is_flag=True,
              help=(
                  'When --global is selected, this assumes admin rights are '
                  'already enabled and therefore sudo/runas will not be used.'
              ))
@click.option('-f', '--force', is_flag=True,
              help='Forces the use of newer features in global updates.')
@click.option('-d', '--dev', is_flag=True,
              help='When locating a requirements file, only use the dev version.')
@click.option('-m', '--module', 'as_module', is_flag=True,
              help=(
                  'Invokes `pip` as a module instead of directly, i.e. '
                  '`python -m pip`.'
              ))
@click.option('--self', is_flag=True, help='Updates `hatch` itself.')
@click.option('-q', '--quiet', is_flag=True, help='Decreases verbosity.')
def update(packages, no_detect, env_name, eager, all_packages, infra, global_install,
           admin, force, dev, as_module, self, quiet):
    """If the option --env is supplied, the update will be applied using
    that named virtual env. Unless the option --global is selected, the
    update will only affect the current user. Of course, this will have
    no effect if a virtual env is in use. The desired name of the admin
    user can be set with the `_DEFAULT_ADMIN_` environment variable.

    When performing a global update, your system may use an older version
    of pip that is incompatible with some features such as --eager. To
    force the use of these features, use --force.

    With no packages nor options selected, this will update packages by
    looking for a `requirements.txt` or a dev version of that in the current
    directory.

    If no --env is chosen, this will attempt to detect a project and use its
    virtual env before resorting to the default pip. No project detection
    will occur if a virtual env is active.

    To update this tool, use the --self flag. All other methods of updating will
    ignore `hatch`. See: https://github.com/pypa/pip/issues/1299
    """
    command = ['install', '--upgrade'] + (['-q'] if quiet else [])
    if not global_install or force:  # no cov
        command.extend(['--upgrade-strategy', 'eager' if eager else 'only-if-needed'])

    infra_packages = ['pip', 'setuptools', 'wheel']
    temp_dir = None

    # Windows' `runas` allows only a single argument for the
    # command so we catch this case and turn our command into
    # a string later.
    windows_admin_command = None

    if self:  # no cov
        as_module = True

    if not self and env_name:
        venv_dir = os.path.join(get_venv_dir(), env_name)
        if not os.path.exists(venv_dir):
            echo_failure('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            executable = (
                [get_proper_python(), '-m', 'pip']
                if as_module or (infra and ON_WINDOWS)
                else [get_proper_pip()]
            )
            command = executable + command
            if all_packages:
                installed_packages = infra_packages if infra else get_installed_packages()
            else:
                installed_packages = None
    elif not self and not venv_active() and not no_detect and is_project():
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
            executable = (
                [get_proper_python(), '-m', 'pip']
                if as_module or (infra and ON_WINDOWS)
                else [get_proper_pip()]
            )
            command = executable + command
            if all_packages:
                installed_packages = infra_packages if infra else get_installed_packages()
            else:
                installed_packages = None
    else:
        venv_dir = None
        executable = (
            [sys.executable if self else get_proper_python(), '-m', 'pip']
            if as_module or (infra and ON_WINDOWS)
            else [get_proper_pip()]
        )
        command = executable + command
        if all_packages:
            installed_packages = infra_packages if infra else get_installed_packages()
        else:
            installed_packages = None

        if not venv_active():  # no cov
            if global_install:
                if not admin:
                    if ON_WINDOWS:
                        windows_admin_command = get_admin_command()
                    else:
                        command = get_admin_command() + command
            else:
                command.append('--user')

    if self:  # no cov
        command.append('hatch')
        if ON_WINDOWS:
            echo_warning('After the update you may want to press Enter to flush stdout.')
            subprocess.Popen(command, shell=NEED_SUBPROCESS_SHELL)
            sys.exit()
        else:
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
            sys.exit(result.returncode)
    elif infra:
        command.extend(infra_packages)
    elif all_packages:
        installed_packages = [
            package for package in installed_packages
            if package not in infra_packages and package != 'hatch'
        ]
        if not installed_packages:
            echo_failure('No packages installed.')
            sys.exit(1)
        command.extend(installed_packages)
    elif packages:
        packages = [package for package in packages if package != 'hatch']
        if not packages:
            echo_failure('No packages to install.')
            sys.exit(1)
        command.extend(packages)

    # When https://github.com/pypa/pipfile is finalized, we'll use it.
    else:
        reqs = get_requirements_file(os.getcwd(), dev=dev)
        if not reqs:
            echo_failure('Unable to locate a requirements file.')
            sys.exit(1)

        with open(reqs, 'r') as f:
            lines = f.readlines()

        matches = []
        for line in lines:
            match = re.match(r'^[^=<>]+', line.lstrip())
            if match and match.group(0) == 'hatch':
                matches.append(line)

        if matches:
            for line in matches:
                lines.remove(line)

            temp_dir = TemporaryDirectory()
            reqs = os.path.join(temp_dir.name, basepath(reqs))

            with open(reqs, 'w') as f:
                f.writelines(lines)

        command.extend(['-r', reqs])

    if windows_admin_command:  # no cov
        command = windows_admin_command + [' '.join(command)]

    if venv_dir:
        with venv(venv_dir):
            if env_name:
                echo_waiting('Updating virtual env `{}`...'.format(env_name))
            else:
                echo_waiting('Updating for this project...')
            result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    else:
        echo_waiting('Updating...')
        result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)

    if temp_dir is not None:
        temp_dir.cleanup()

    sys.exit(result.returncode)
