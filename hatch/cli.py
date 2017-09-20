import os
import subprocess
import sys
from tempfile import TemporaryDirectory

import click

from hatch.commands import (
    conda, python, config, new, init, install, uninstall, grow, update, test,
    build, clean, release
)
from hatch.commands.utils import (
    CONTEXT_SETTINGS, UNKNOWN_OPTIONS, echo_failure, echo_info, echo_success,
    echo_warning, echo_waiting
)
from hatch.env import (
    get_editable_packages, get_editable_package_location, get_python_version,
    get_python_implementation, install_packages
)
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, load_settings, save_settings
)
from hatch.shells import run_shell
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, get_random_venv_name, remove_path, resolve_path
)
from hatch.venv import (
    VENV_DIR, clone_venv, create_venv, fix_available_venvs, get_available_venvs,
    is_venv, venv
)


class AliasedGroup(click.Group):  # no cov
    def get_command(self, ctx, cmd_name):
        if cmd_name == 'use':
            return shell
        return click.Group.get_command(self, ctx, cmd_name)


@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
@click.version_option()
def hatch():
    pass


hatch.add_command(build)
hatch.add_command(conda)
hatch.add_command(config)
hatch.add_command(grow)
hatch.add_command(init)
hatch.add_command(install)
hatch.add_command(new)
hatch.add_command(python)
hatch.add_command(test)
hatch.add_command(uninstall)
hatch.add_command(update)
hatch.add_command(clean)
hatch.add_command(release)


def list_pypaths(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    try:
        settings = load_settings()
    except FileNotFoundError:
        echo_failure('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    pypaths = settings.get('pypaths', {})
    if pypaths:
        for p in pypaths:
            echo_success('{} -> '.format(p), nl=False)
            echo_info('{}'.format(pypaths[p]))
    else:
        echo_failure('There are no saved Python paths. Add '
                     'one via `hatch pypath NAME PATH`.')

    ctx.exit()


@hatch.command('pypath', context_settings=CONTEXT_SETTINGS,
               short_help='Names a Python path or shows available ones')
@click.argument('name')
@click.argument('path')
@click.option('-l', '--list', 'show', is_flag=True, is_eager=True, callback=list_pypaths,
              help='Shows available Python paths.')
def python_path(name, path, show):
    """Names an absolute path to a Python executable. You can also modify
    these in the config file entry `pypaths`.

    Hatch can then use these paths by name when creating virtual envs, building
    packages, etc.

    \b
    $ hatch pypath -l
    There are no saved Python paths. Add one via `hatch pypath NAME PATH`.
    $ hatch pypath py2 /usr/bin/python
    Successfully saved Python `py2` located at `/usr/bin/python`.
    $ hatch pypath py3 /usr/bin/python3
    Successfully saved Python `py3` located at `/usr/bin/python3`.
    $ hatch pypath -l
    py2 -> /usr/bin/python
    py3 -> /usr/bin/python3
    """
    try:
        settings = load_settings()
    except FileNotFoundError:
        echo_failure('Unable to locate config file. Try `hatch config --restore`.')
        sys.exit(1)

    if 'pypaths' not in settings:
        updated_settings = copy_default_settings()
        updated_settings.update(settings)
        settings = updated_settings
        echo_success('Settings were successfully updated to include `pypaths` entry.')

    settings['pypaths'][name] = path
    save_settings(settings)
    echo_success('Successfully saved Python `{}` located at `{}`.'.format(name, path))


def list_envs(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    venvs = get_available_venvs()

    if venvs:
        echo_success('Virtual environments found in `{}`:\n'.format(VENV_DIR))
        for venv_name, venv_dir in venvs:
            with venv(venv_dir):
                echo_success('{} ->'.format(venv_name))
                if value == 1:
                    echo_info('  Version: {}'.format(get_python_version()))
                elif value == 2:
                    echo_info('  Version: {}'.format(get_python_version()))
                    echo_info('  Implementation: {}'.format(get_python_implementation()))
                else:
                    echo_info('  Version: {}'.format(get_python_version()))
                    echo_info('  Implementation: {}'.format(get_python_implementation()))
                    echo_info('  Local packages: {}'.format(', '.join(sorted(get_editable_packages()))))

    # I don't want to move users' virtual environments
    # temporarily for tests as one may be in use.
    else:  # no cov
        echo_failure('No virtual environments found in `{}`. To create '
                     'one do `hatch env NAME`.'.format(VENV_DIR))

    ctx.exit()


def restore_envs(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    fix_available_venvs()
    echo_success('Successfully restored all available virtual envs.')
    ctx.exit()


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help='Manages virtual environments')
@click.argument('name')
@click.option('-py', '--python', 'pyname',
              help='The named Python path to use. This overrides --pypath.')
@click.option('-pp', '--pypath',
              help='An absolute path to a Python executable.')
@click.option('-c', '--clone',
              help='Specifies an existing virtual env to clone. (Experimental)')
@click.option('-v', '--verbose', is_flag=True, help='Increases verbosity.')
@click.option('-r', '--restore', is_flag=True, is_eager=True, callback=restore_envs,
              help=(
                  'Attempts to make all virtual envs in `{}` usable by '
                  'fixing the executable paths in scripts and removing '
                  'all compiled `*.pyc` files. (Experimental)'.format(VENV_DIR)
              ))
@click.option('-l', '--list', 'show', count=True, is_eager=True, callback=list_envs,
              help=(
                  'Shows available virtual envs. Can stack up to 3 times to '
                  'show more info.'
              ))
def env(name, pyname, pypath, clone, verbose, restore, show):
    """Creates a new virtual env that can later be utilized with the
    `shell` command.

    \b
    $ hatch pypath -l
    py2 -> /usr/bin/python
    py3 -> /usr/bin/python3
    $ hatch env -l
    No virtual environments found in /home/ofek/.virtualenvs. To create one do `hatch env NAME`.
    $ hatch env my-app
    Already using interpreter /usr/bin/python3
    Successfully saved virtual env `my-app` to `/home/ofek/.virtualenvs/my-app`.
    $ hatch env -py py2 old
    Successfully saved virtual env `old` to `/home/ofek/.virtualenvs/old`.
    $ hatch env -pp ~/pypy3/bin/pypy fast
    Successfully saved virtual env `fast` to `/home/ofek/.virtualenvs/fast`.
    $ hatch env -ll
    Virtual environments found in /home/ofek/.virtualenvs:

    \b
    fast ->
      Version: 3.5.3
      Implementation: PyPy
    my-app ->
      Version: 3.5.2
      Implementation: CPython
    old ->
      Version: 2.7.12
      Implementation: CPython
    """
    if pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:
            echo_failure('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        pypath = settings.get('pypaths', {}).get(pyname, None)
        if not pypath:
            echo_failure('Unable to find a Python path named `{}`.'.format(pyname))
            sys.exit(1)

    venv_dir = os.path.join(VENV_DIR, name)
    if os.path.exists(venv_dir):
        echo_failure('Virtual env `{name}` already exists. To remove '
                     'it do `hatch shed -e {name}`.'.format(name=name))
        sys.exit(1)

    if not clone and not pyname and pypath and not os.path.exists(pypath):
        echo_failure('Python path `{}` does not exist. Be sure to use the absolute path '
                     'e.g. `/usr/bin/python` instead of simply `python`.'.format(pypath))
        sys.exit(1)

    if clone:
        origin = os.path.join(VENV_DIR, clone)
        if not os.path.exists(origin):
            echo_failure('Virtual env `{name}` does not exist.'.format(name=clone))
            sys.exit(1)
        echo_waiting('Cloning virtual env `{}`...'.format(clone))
        clone_venv(origin, venv_dir)
        echo_success('Successfully cloned virtual env `{}` from `{}` to `{}`.'.format(name, clone, venv_dir))
    else:
        echo_waiting('Creating virtual env `{}`...'.format(name))
        create_venv(venv_dir, pypath, verbose=verbose)
        echo_success('Successfully saved virtual env `{}` to `{}`.'.format(name, venv_dir))


@hatch.command(context_settings=CONTEXT_SETTINGS,
               short_help='Removes named Python paths or virtual environments')
@click.option('-p', '-py', '--pypath', 'pyname',
              help='Forward-slash-separated list of named Python paths.')
@click.option('-e', '--env', 'env_name',
              help='Forward-slash-separated list of named virtual envs.')
@click.pass_context
def shed(ctx, pyname, env_name):
    """Removes named Python paths or virtual environments.

    \b
    $ hatch pypath -l
    py2 -> /usr/bin/python
    py3 -> /usr/bin/python3
    invalid -> :\/:
    $ hatch env -ll
    Virtual environments found in /home/ofek/.virtualenvs:

    \b
    duplicate ->
      Version: 3.5.2
      Implementation: CPython
    fast ->
      Version: 3.5.3
      Implementation: PyPy
    my-app ->
      Version: 3.5.2
      Implementation: CPython
    old ->
      Version: 2.7.12
      Implementation: CPython
    $ hatch shed -p invalid -e duplicate/old
    Successfully removed Python path named `invalid`.
    Successfully removed virtual env named `duplicate`.
    Successfully removed virtual env named `old`.
    """
    if not (pyname or env_name):
        click.echo(ctx.get_help())
        return

    if pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:
            echo_failure('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        for pyname in pyname.split('/'):
            pypath = settings.get('pypaths', {}).pop(pyname, None)
            if pypath is not None:
                save_settings(settings)
                echo_success('Successfully removed Python path named `{}`.'.format(pyname))
            else:
                echo_warning('Python path named `{}` already does not exist.'.format(pyname))

    if env_name:
        for env_name in env_name.split('/'):
            venv_dir = os.path.join(VENV_DIR, env_name)
            if os.path.exists(venv_dir):
                remove_path(venv_dir)
                echo_success('Successfully removed virtual env named `{}`.'.format(env_name))
            else:
                echo_warning('Virtual env named `{}` already does not exist.'.format(env_name))


@hatch.command(context_settings=UNKNOWN_OPTIONS,
               short_help='Activates or sends a command to a virtual environment')
@click.argument('env_name', required=False, default='')
@click.argument('command', required=False, nargs=-1, type=click.UNPROCESSED)
@click.option('-s', '--shell', 'shell_name',
              help=(
                  'The name of shell to use e.g. `bash`. If the shell name '
                  'is not supported, e.g. `bash -O`, it will be treated as '
                  'a command and no custom prompt will be provided. This '
                  'overrides the config file entry `shell`.'
              ))
@click.option('-t', '--temp', 'temp_env', is_flag=True,
              help='Use a new temporary virtual env.')
@click.option('-py', '--python', 'pyname',
              help=(
                  'A named Python path to use when creating a temporary '
                  'virtual env. This overrides --pypath.'
              ))
@click.option('-pp', '--pypath',
              help=(
                  'An absolute path to a Python executable to use when '
                  'creating a temporary virtual env.'
              ))
def shell(env_name, command, shell_name, temp_env, pyname, pypath):  # no cov
    """Activates or sends a command to a virtual environment. A default shell
    name (or command) can be specified in the config file entry `shell` or the
    environment variable `SHELL`. If there is no entry, env var, nor shell
    option provided, a system default will be used: `cmd` on Windows, `bash`
    otherwise.

    Any arguments provided after the first will be sent to the virtual env as
    a command without activating it. If there is only the env without args,
    it will be activated similarly to how you are accustomed. The name of
    the virtual env to use must be omitted if using the --temp env option.
    If no env is chosen, this will attempt to detect a project and activate
    its virtual env. To run a command in a project's virtual env, use `.` as
    the env name.

    Activation will not do anything to your current shell, but will rather
    spawn a subprocess to avoid any unwanted strangeness occurring in your
    current environment. If you would like to learn more about the benefits
    of this approach, be sure to read https://gist.github.com/datagrok/2199506.
    To leave a virtual env, type `exit`, or you can do `Ctrl+D` on non-Windows
    machines.

    `use` is an alias for this command.

    \b
    Activation:
    $ hatch env -ll
    Virtual environments found in `/home/ofek/.virtualenvs`:

    \b
    fast ->
      Version: 3.5.3
      Implementation: PyPy
    my-app ->
      Version: 3.5.2
      Implementation: CPython
    old ->
      Version: 2.7.12
      Implementation: CPython
    $ which python
    /usr/bin/python
    $ hatch shell my-app
    (my-app) $ which python
    /home/ofek/.virtualenvs/my-app/bin/python

    \b
    Commands:
    $ hatch shell my-app pip list --format=columns
    Package    Version
    ---------- -------
    pip        9.0.1
    setuptools 36.3.0
    wheel      0.29.0
    $ hatch shell my-app hatch install -q requests six
    $ hatch shell my-app pip list --format=columns
    Package    Version
    ---------- -----------
    certifi    2017.7.27.1
    chardet    3.0.4
    idna       2.6
    pip        9.0.1
    requests   2.18.4
    setuptools 36.3.0
    six        1.10.0
    urllib3    1.22
    wheel      0.29.0

    \b
    Temporary env:
    $ hatch shell -t
    Already using interpreter /usr/bin/python3
    Using base prefix '/usr'
    New python executable in /tmp/tmpzg73untp/Ihqd/bin/python3
    Also creating executable in /tmp/tmpzg73untp/Ihqd/bin/python
    Installing setuptools, pip, wheel...done.
    $ which python
    /tmp/tmpzg73untp/Ihqd/bin/python
    """
    venv_dir = None
    if resolve_path(env_name) == os.getcwd():
        env_name = ''

    if not (env_name or temp_env):
        if os.path.isfile(os.path.join(os.getcwd(), 'setup.py')):
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
        else:
            echo_failure('No project found.')
            sys.exit(1)

    if env_name and temp_env:
        echo_failure('Cannot use more than one virtual env at a time!')
        sys.exit(1)

    if not command and '_HATCHING_' in os.environ:
        echo_failure(
            'Virtual environments cannot be nested, sorry! To leave '
            'the current one type `exit` or press `Ctrl+D`.'
        )
        sys.exit(1)

    if temp_env:
        if pyname:
            try:
                settings = load_settings()
            except FileNotFoundError:
                echo_failure('Unable to locate config file. Try `hatch config --restore`.')
                sys.exit(1)

            pypath = settings.get('pypaths', {}).get(pyname, None)
            if not pypath:
                echo_failure('Unable to find a Python path named `{}`.'.format(pyname))
                sys.exit(1)

        temp_dir = TemporaryDirectory()
        env_name = get_random_venv_name()
        venv_dir = os.path.join(temp_dir.name, env_name)
        echo_waiting('Creating a temporary virtual env named `{}`...'.format(env_name))
        create_venv(venv_dir, pypath=pypath, verbose=True)
    else:
        temp_dir = None
        venv_dir = venv_dir or os.path.join(VENV_DIR, env_name)
        if not os.path.exists(venv_dir):
            echo_failure('Virtual env named `{}` does not exist.'.format(env_name))
            sys.exit(1)

    result = None

    try:
        if command:
            with venv(venv_dir):
                echo_waiting('Running `{}` in {}...'.format(
                    ' '.join(c if len(c.split()) == 1 else '"{}"'.format(c) for c in command),
                    '`{}`'.format(env_name) if env_name else "this project's env"
                ))
                result = subprocess.run(command, shell=NEED_SUBPROCESS_SHELL).returncode
        else:
            with venv(venv_dir) as exe_dir:
                result = run_shell(exe_dir, shell_name)
    finally:
        result = 1 if result is None else result
        if temp_dir is not None:
            temp_dir.cleanup()

    sys.exit(result)
