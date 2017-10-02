import os
import sys

import click

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_success, echo_waiting, echo_warning
)
from hatch.config import get_venv_dir
from hatch.create import create_package
from hatch.env import install_packages
from hatch.settings import copy_default_settings, load_settings
from hatch.utils import chdir
from hatch.venv import create_venv, venv


@click.command(context_settings=CONTEXT_SETTINGS,
               short_help='Creates a new Python project')
@click.argument('name', required=False)
@click.option('-ne', '--no-env', is_flag=True,
              help=(
                  'Disables the creation of a dedicated virtual env.'
              ))
@click.option('-py', '--python', 'pyname',
              help=(
                  'A named Python path to use when creating a virtual '
                  'env. This overrides --pypath.'
              ))
@click.option('-pp', '--pypath',
              help=(
                  'An absolute path to a Python executable to use when '
                  'creating a virtual env.'
              ))
@click.option('-g', '--global-packages', is_flag=True,
              help='Gives created virtual envs access to the global site-packages.')
@click.option('-e', '--env', 'env_name',
              help=(
                  'Forward-slash-separated list of named virtual envs to be '
                  "installed in. Will create any that don't already exist."
              ))
@click.option('--basic', is_flag=True,
              help='Disables third-party services and readme badges.')
@click.option('--cli', is_flag=True,
              help=(
                  'Creates a `cli.py` in the package directory and an entry '
                  'point in `setup.py` pointing to the properly named function '
                  'within. Also, a `__main__.py` is created so it can be '
                  'invoked via `python -m pkg_name`.'
              ))
@click.option('-l', '--licenses',
              help='Comma-separated list of licenses to use.')
@click.option('-i', '--interactive', is_flag=True, help='Invokes interactive mode.')
def new(name, no_env, pyname, pypath, global_packages, env_name, basic, cli,
        licenses, interactive):
    """Creates a new Python project.

    Values from your config file such as `name` and `pyversions` will be used
    to help populate fields. You can also specify things like the readme format
    and which CI service files to create. All options override the config file.

    By default a virtual env will be created in the project directory and will
    install the project locally so any edits will auto-update the installation.
    You can also locally install the created project in other virtual envs using
    the --env option.

    Here is an example using an unmodified config file:

    \b
    $ hatch new my-app
    Created project `my-app`
    $ tree --dirsfirst my-app
    my-app
    ├── my_app
    │   └── __init__.py
    ├── tests
    │   └── __init__.py
    ├── LICENSE-APACHE
    ├── LICENSE-MIT
    ├── MANIFEST.in
    ├── README.rst
    ├── requirements.txt
    ├── setup.py
    └── tox.ini

    2 directories, 8 files
    """
    try:
        settings = load_settings()
    except FileNotFoundError:
        settings = copy_default_settings()
        echo_warning(
            'Unable to locate config file; try `hatch config --restore`. '
            'The default project structure will be used.'
        )

    origin = os.getcwd()
    package_name = name or click.prompt('Project name')

    d = os.path.join(origin, package_name)
    if os.path.exists(d):
        echo_failure('Directory `{}` already exists.'.format(d))
        sys.exit(1)

    if interactive or not name:
        settings['version'] = click.prompt('Version', default='0.0.1')
        settings['description'] = click.prompt('Description', default='')
        settings['name'] = click.prompt('Author', default=settings.get('name', ''))
        settings['email'] = click.prompt("Author's email", default=settings.get('email', ''))
        licenses = click.prompt('License(s)', default=licenses or 'mit,apache2')

    if licenses:
        settings['licenses'] = [str.strip(li) for li in licenses.split(',')]

    if basic:
        settings['basic'] = True

    settings['cli'] = cli

    venvs = env_name.split('/') if env_name else []
    if (venvs or not no_env) and pyname:
        try:
            settings = load_settings()
        except FileNotFoundError:  # no cov
            echo_failure('Unable to locate config file. Try `hatch config --restore`.')
            sys.exit(1)

        pypath = settings.get('pypaths', {}).get(pyname, None)
        if not pypath:
            echo_failure('Unable to find a Python path named `{}`.'.format(pyname))
            sys.exit(1)

    os.makedirs(d)
    with chdir(d, cwd=origin):
        create_package(d, package_name, settings)
        echo_success('Created project `{}`'.format(package_name))

        if not no_env:
            venv_dir = os.path.join(d, 'venv')
            echo_waiting('Creating its own virtual env... ', nl=False)
            create_venv(venv_dir, pypath=pypath, use_global=global_packages)
            echo_success('complete!')

            with venv(venv_dir):
                echo_waiting('Installing locally in the virtual env... ', nl=False)
                install_packages(['-q', '-e', '.'])
                echo_success('complete!')

        for vname in venvs:
            venv_dir = os.path.join(get_venv_dir(), vname)
            if not os.path.exists(venv_dir):
                echo_waiting('Creating virtual env `{}`... '.format(vname), nl=False)
                create_venv(venv_dir, pypath=pypath, use_global=global_packages)
                echo_success('complete!')

            with venv(venv_dir):
                echo_waiting('Installing locally in virtual env `{}`... '.format(vname), nl=False)
                install_packages(['-q', '-e', '.'])
                echo_success('complete!')
