import os

import click

from hatch.core import create_package
from hatch.settings import load_settings


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
def new(name, basic, cli):
    settings = load_settings()

    if basic:
        settings['basic'] = True

    settings['cli'] = cli

    d = os.path.join(os.getcwd(), name)

    if os.path.exists(d):
        click.echo('Directory {} already exists.'.format(d))
        return

    os.makedirs(d)
    os.chdir(d)

    create_package(d, name, settings)


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


@hatch.command(name='set', context_settings=CONTEXT_SETTINGS)
@click.option('-n', '--name')
@click.option('-e', '--email')
def set_defaults(name, email):
    click.echo(name)
