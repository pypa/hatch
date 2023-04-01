import click
from hatchling.plugin import hookimpl


@click.command(short_help="Execute a custom command")
def random():
    """Execute a custom command"""
    click.echo("random")


@hookimpl
def hatch_register_commands():
    return [random]
