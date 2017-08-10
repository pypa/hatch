import json
import io
import os
import subprocess
import sys
import time
from tempfile import TemporaryDirectory

import click
from atomicwrites import atomic_write
from twine.utils import DEFAULT_REPOSITORY, TEST_REPOSITORY

from hatch.build import build_package
from hatch.clean import clean_package
from hatch.create import create_package
from hatch.env import (
    get_editable_package_location, get_installed_packages, get_python_version,
    get_python_implementation
)
from hatch.grow import BUMP, bump_package_version
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, load_settings, restore_settings,
    save_settings
)
from hatch.shells import IMMORTAL_SHELLS, get_default_shell_info, get_shell_command
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, basepath, chdir, get_proper_pip,
    get_proper_python, remove_path, venv_active
)
from hatch.venv import VENV_DIR, create_venv, venv


CONTEXT_SETTINGS = {
    'max_content_width': 300
}
UNKNOWN_OPTIONS = {
    'max_content_width': 300,
    'ignore_unknown_options': True
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
    try:
        settings = load_settings()
    except FileNotFoundError:
        click.echo('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

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
    try:
        settings = load_settings()
    except FileNotFoundError:
        click.echo('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    if basic:
        settings['basic'] = True

    settings['cli'] = cli

    create_package(os.getcwd(), name, settings)
    click.echo('Created project `{}` here'.format(name))


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.option('-u', '--update', 'update_settings', is_flag=True)
@click.option('--restore', is_flag=True)
def config(update_settings, restore):
    if update_settings:
        try:
            user_settings = load_settings()
            updated_settings = copy_default_settings()
            updated_settings.update(user_settings)
            save_settings(updated_settings)
            click.echo('Settings were successfully updated.')
        except FileNotFoundError:
            restore = True

    if restore:
        restore_settings()
        click.echo('Settings were successfully restored.')

    click.echo('Settings location: ' + SETTINGS_FILE)


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.option('--eager', is_flag=True)
@click.option('--all', 'all_packages', is_flag=True)
@click.option('-g', '--global', 'global_install', is_flag=True)
def update(eager, all_packages, global_install):
    command = [
        get_proper_pip(), 'install', '--upgrade', '--upgrade-strategy',
        'eager' if eager else 'only-if-needed'
    ]

    if not venv_active() and not global_install and not NEED_SUBPROCESS_SHELL:  # no cov
        command.append('--user')

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
        relative_path = os.path.join(os.getcwd(), basepath(path))
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
        relative_path = os.path.join(os.getcwd(), basepath(path))
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.getcwd()

    python_cmd = [get_proper_python(), '-m'] if env_aware else []
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


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('package', required=False)
@click.option('-p', '--path')
@click.option('-v', '--verbose', is_flag=True)
def clean(package, path, verbose):
    if package:
        path = get_editable_package_location(package)
        if not path:
            click.echo('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        relative_path = os.path.join(os.getcwd(), basepath(path))
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.getcwd()

    removed_paths = clean_package(path, editable=package)

    if verbose:
        if removed_paths:
            click.echo('Removed paths:')
            for p in removed_paths:
                click.echo(p)


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('package', required=False)
@click.option('-p', '--path')
@click.option('-u', '--universal', is_flag=True)
@click.option('-n', '--name')
@click.option('-d', '--build-dir')
@click.option('-c', '--clean', 'clean_first', is_flag=True)
def build(package, path, universal, name, build_dir, clean_first):
    if package:
        path = get_editable_package_location(package)
        if not path:
            click.echo('`{}` is not an editable package.'.format(package))
            sys.exit(1)
    elif path:
        relative_path = os.path.join(os.getcwd(), basepath(path))
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.getcwd()

    if clean_first:
        clean_package(path)

    sys.exit(build_package(path, universal, name, build_dir))


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('package', required=False)
@click.option('-p', '--path')
@click.option('-u', '--username')
@click.option('-t', '--test', 'test_pypi', is_flag=True)
@click.option('-s', '--strict', is_flag=True)
def release(package, path, username, test_pypi, strict):
    if package:
        path = get_editable_package_location(package)
        if not path:
            click.echo('`{}` is not an editable package.'.format(package))
            sys.exit(1)
        path = os.path.join(path, 'dist')
    elif path:
        relative_path = os.path.join(os.getcwd(), basepath(path))
        if os.path.exists(relative_path):
            path = relative_path
        elif not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)
    else:
        path = os.path.join(os.getcwd(), 'dist')
        if not os.path.exists(path):
            click.echo('Directory `{}` does not exist.'.format(path))
            sys.exit(1)

    if not username:
        try:
            settings = load_settings()
        except FileNotFoundError:
            click.echo('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        username = settings.get('pypi_username', None)
        if not username:
            click.echo(
                'A username must be supplied via -u/--username or '
                'in {} as pypi_username.'.format(SETTINGS_FILE)
            )
            sys.exit(1)

    command = ['twine', 'upload', '{}{}*'.format(path, os.path.sep), '-u', username]

    if test_pypi:
        command.extend(['-r', TEST_REPOSITORY, '--repository-url', TEST_REPOSITORY])
    else:  # no cov
        command.extend(['-r', DEFAULT_REPOSITORY, '--repository-url', DEFAULT_REPOSITORY])

    if not strict:
        command.append('--skip-existing')

    result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
    sys.exit(result.returncode)


def list_pythons(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    try:
        settings = load_settings()
    except FileNotFoundError:
        click.echo('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    pythons = settings.get('pythons', {})
    if pythons:
        for p in pythons:
            click.echo('{} -> {}'.format(p, pythons[p]))
    else:
        click.echo('There are no saved Python paths. Add '
                   'one via `hatch python NAME PATH`.')

    ctx.exit()


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('name')
@click.argument('path')
@click.option('-l', '--list', 'show', is_flag=True, is_eager=True, callback=list_pythons)
def python(name, path, show):
    try:
        settings = load_settings()
    except FileNotFoundError:
        click.echo('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    if 'pythons' not in settings:
        updated_settings = copy_default_settings()
        updated_settings.update(settings)
        settings = updated_settings
        click.echo('Settings were successfully updated to include `pythons` entry.')

    settings['pythons'][name] = path
    save_settings(settings)
    click.echo('Successfully saved Python `{}` located at `{}`.'.format(name, path))


def list_envs(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    venv_names = [
        path for path in os.listdir(VENV_DIR)
        if os.path.isdir(os.path.join(VENV_DIR, path))
    ] if os.path.exists(VENV_DIR) else None

    if venv_names:
        click.echo('Virtual environments found in {}:\n'.format(VENV_DIR))
        for name in venv_names:
            with venv(os.path.join(VENV_DIR, name)):
                click.echo(
                    '{} ->\n'
                    '  Version: {}\n'
                    '  Implementation: {}'.format(
                        name, get_python_version(), get_python_implementation()
                    )
                )

    # I don't want move users' virtual environments
    # temporarily for tests as one may be in use.
    else:  # no cov
        click.echo('No virtual environments found in {}. To create '
                   'one do `hatch env NAME`.'.format(VENV_DIR))

    ctx.exit()


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.argument('name')
@click.option('-p', '--python', 'pyname')
@click.option('-pp', '--pypath')
@click.option('-l', '--list', 'show', is_flag=True, is_eager=True, callback=list_envs)
def env(name, pyname, pypath, show):
    if pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:
            click.echo('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        pypath = settings.get('pythons', {}).get(pyname, None)
        if not pypath:
            click.echo('Unable to find a Python path named `{}`.'.format(pyname))
            sys.exit(1)

    venv_dir = os.path.join(VENV_DIR, name)
    if os.path.exists(venv_dir):
        click.echo('Virtual env `{name}` already exists. To remove '
                   'it do `hatch shed -e {name}`.'.format(name=name))
        sys.exit(1)

    if not pyname and pypath and not os.path.exists(pypath):
        click.echo('Python path `{}` does not exist. Be sure to use the absolute path '
                   'e.g. `/usr/bin/python` instead of simply `python`.'.format(pypath))
        sys.exit(1)

    create_venv(venv_dir, pypath)
    click.echo('Successfully saved virtual env `{}` to `{}`.'.format(name, venv_dir))


@hatch.command(context_settings=CONTEXT_SETTINGS)
@click.option('-p', '--python', 'pyname')
@click.option('-e', '--env', 'env_name')
@click.pass_context
def shed(ctx, pyname, env_name):
    if not (pyname or env_name):
        click.echo(ctx.get_help())
        return

    if pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:
            click.echo('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        pypath = settings.get('pythons', {}).pop(pyname, None)
        if pypath is not None:
            click.echo('Successfully removed Python path named `{}`.'.format(pyname))
            save_settings(settings)
        else:
            click.echo('Python path named `{}` already does not exist.'.format(pyname))
    else:
        venv_dir = os.path.join(VENV_DIR, env_name)
        if os.path.exists(venv_dir):
            remove_path(venv_dir)
            click.echo('Successfully removed virtual env named `{}`.'.format(env_name))
        else:
            click.echo('Virtual env named `{}` already does not exist.'.format(env_name))


@hatch.command(context_settings=UNKNOWN_OPTIONS)
@click.argument('env_name')
@click.argument('command', required=False, nargs=-1, type=click.UNPROCESSED)
@click.option('-s', '--shell')
@click.option('--nest/--kill', '-n/-k', default=None)
def use(env_name, command, shell, nest):  # no cov

    # Run commands regardless of virtual env activation.
    if command:
        venv_dir = os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            click.echo('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            subprocess.run(command, shell=NEED_SUBPROCESS_SHELL)
        return

    try:
        settings = load_settings()
    except FileNotFoundError:
        settings = {}

    shell_name, shell_path = get_default_shell_info(shell, settings)

    if shell_name in IMMORTAL_SHELLS or nest or (nest is None and settings.get('nest_shells')):
        venv_dir = os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            click.echo('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

        with venv(venv_dir):
            with get_shell_command(env_name, shell_name, shell_path, nest=True) as shell_command:
                subprocess.run(shell_command, shell=NEED_SUBPROCESS_SHELL)
        return

    # If in activated venv shell, notify main loop and exit.
    if '_HATCH_FILE_' in os.environ:
        with atomic_write(os.environ['_HATCH_FILE_'], overwrite=True) as f:
            data = json.dumps({
                'env_name': env_name,
                'shell': shell
            })
            f.write(data)
        return

    with TemporaryDirectory() as d:
        communication_file = os.path.join(d, 'temp.json')
        evars = {'_HATCH_FILE_': communication_file}

        while True:
            venv_dir = os.path.join(VENV_DIR, env_name)
            if not os.path.exists(venv_dir):
                click.echo('Virtual env named `{}` does not exist.'.format(env_name))
                sys.exit(1)

            shell_name, shell_path = get_default_shell_info(shell)

            with venv(venv_dir, evars=evars):
                try:
                    with get_shell_command(env_name, shell_name, shell_path) as shell_command:
                        process = subprocess.Popen(shell_command)
                        while True:
                            if process.poll() is not None:
                                return

                            if os.path.exists(communication_file):

                                # This is necessary on non-Windows machines.
                                #
                                # Killing a spawned shell suspends execution of
                                # this script due to competition for terminal use.
                                # Termination works, however only if the spawned
                                # shell has no active processes. Therefore, we sleep
                                # shortly to ensure the second `hatch use ...` has
                                # time to write the communication file and exit.
                                if not NEED_SUBPROCESS_SHELL:
                                    time.sleep(0.2)

                                with open(communication_file, 'r') as f:
                                    args = json.loads(f.read())
                                env_name = args['env_name']
                                shell = args['shell']

                                remove_path(communication_file)
                                process.terminate()
                                break
                except KeyboardInterrupt:
                    break










