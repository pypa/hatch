import click

from hatch.cli.project.metadata import metadata


@click.group(short_help='View project information')
def project():
    pass


project.add_command(metadata)
