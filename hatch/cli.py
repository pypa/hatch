import io
import os
import subprocess
import sys

import click

from hatch.create import create_package
from hatch.env import get_editable_package_location, get_installed_packages
from hatch.grow import BUMP, bump_package_version
from hatch.settings import SETTINGS_FILE, load_settings, restore_settings
from hatch.utils import NEED_SUBPROCESS_SHELL, chdir


CONTEXT_SETTINGS = {
    'max_content_width': 300
}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def hatch():
    pass


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('name')
@click.option('--basic', is_flag=True)
@click.option('--cli', is_flag=True)
def egg(name, basic, cli):
    settings = load_settings()

    if basic:
        settings['basic'] = True

    settings['cli'] = cli

    origin = os.getcwd()
    d = os.path.join(origin, name)

    if os.path.exists(d):
        click.echo('Directory `{}` already exists.'.format(d))
        sys.exit(1)

    os.makedirs(d)
    with chdir(d, cwd=origin):
        create_package(d, name, settings)
        click.echo('Created project `{}`'.format(name))


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('name')
@click.option('--basic', is_flag=True)
@click.option('--cli', is_flag=True)
def init(name, basic, cli):
    settings = load_settings()

    if basic:
        settings['basic'] = True

    settings['cli'] = cli

    create_package(os.getcwd(), name, settings)
    click.echo('Created project `{}` here'.format(name))


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.option('--restore', is_flag=True)
def config(restore):
    if restore:
        restore_settings()
        click.echo('Settings were successfully restored.')

    click.echo('Settings location: ' + SETTINGS_FILE)


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.option('--eager', is_flag=True)
@click.option('--all', 'all_packages', is_flag=True)
def update(eager, all_packages):
    command = [
        'pip', 'install', '--upgrade', '--upgrade-strategy',
        'eager' if eager else 'only-if-needed'
    ]

    if all_packages:
        installed_packages = get_installed_packages()
        installed_packages = [
            package for package in installed_packages
            if package not in ['pip', 'setuptools', 'wheel']
        ]
        if not installed_packages:
            click.echo('No packages installed.')
            sys.exit(1)
        command.extend(installed_packages)
    else:
        path = os.path.join(os.getcwd(), 'requirements.txt')
        if not os.path.exists(path):
            click.echo('Unable to locate a requirements file.')
            sys.exit(1)
        command.extend(['-r', path])

    subprocess.call(command, shell=NEED_SUBPROCESS_SHELL)


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('part', type=click.Choice(BUMP.keys()))
@click.argument('package', required=False)
@click.option('-p', '--path')
def grow(part, package, path):
    if package:
        path = get_editable_package_location(package)
        if not path:
            click.echo('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        relative_path = os.path.join(
            os.getcwd(),
            os.path.basename(os.path.normpath(path))
        )
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.getcwd()

    f, old_version, new_version = bump_package_version(path, part)

    if new_version:
        click.echo('Updated {}'.format(f))
        click.echo('{} -> {}'.format(old_version, new_version))
    else:
        if f:
            click.echo('Found init files:')
            for file in f:
                click.echo(file)
            click.echo('\nUnable to find a version specifier.')
            sys.exit(1)
        else:
            click.echo('No init files found.')
            sys.exit(1)


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('package', required=False)
@click.option('-p', '--path')
@click.option('-c', '--cov', is_flag=True)
@click.option('-ta', '--test-args', default='')
@click.option('-ca', '--cov-args')
@click.option('-e', '--env-aware', is_flag=True)
def test(package, path, cov, test_args, cov_args, env_aware):
    if package:
        path = get_editable_package_location(package)
        if not path:
            click.echo('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        relative_path = os.path.join(
            os.getcwd(),
            os.path.basename(os.path.normpath(path))
        )
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.getcwd()

    python_cmd = ['python', '-m'] if env_aware else []
    command = python_cmd.copy()

    if cov:
        command.extend(['coverage', 'run'])
        command.extend(cov_args.split() if cov_args is not None else ['--parallel-mode'])
        command.append('-m')

    command.append('pytest')
    command.extend(test_args.split())

    try:  # no cov
        sys.stdout.fileno()
        testing = False
    except io.UnsupportedOperation:  # no cov
        testing = True

    # For testing we need to pipe because Click changes stdio streams.
    stdout = sys.stdout if not testing else subprocess.PIPE
    stderr = sys.stderr if not testing else subprocess.PIPE

    with chdir(path):
        output = b''

        test_result = subprocess.run(
            command,
            stdout=stdout, stderr=stderr,
            shell=NEED_SUBPROCESS_SHELL
        )
        output += test_result.stdout or b''
        output += test_result.stderr or b''

        if cov:
            click.echo('\nTests completed, checking coverage...\n')

            result = subprocess.run(
                python_cmd + ['coverage', 'combine', '--append'],
                stdout=stdout, stderr=stderr,
                shell=NEED_SUBPROCESS_SHELL
            )
            output += result.stdout or b''
            output += result.stderr or b''

            result = subprocess.run(
                python_cmd + ['coverage', 'report', '-m'],
                stdout=stdout, stderr=stderr,
                shell=NEED_SUBPROCESS_SHELL
            )
            output += result.stdout or b''
            output += result.stderr or b''

    if testing:  # no cov
        click.echo(output.decode())
        click.echo(output.decode())

    sys.exit(test_result.returncode)



















