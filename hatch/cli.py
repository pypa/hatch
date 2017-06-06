import click


CONTEXT_SETTINGS = {
    'max_content_width': 300
}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def hatch():
    pass


@hatch.command(name='set', context_settings=CONTEXT_SETTINGS)
@click.option('-n', '--name')
@click.option('-e', '--email')
def set_defaults(name, email):
    click.echo(name)
