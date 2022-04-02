import click

from .create import create
from .find import find
from .prune import prune
from .remove import remove
from .run import run
from .show import show


@click.group(short_help='Manage project environments')
def env():
    pass


env.add_command(create)
env.add_command(find)
env.add_command(prune)
env.add_command(remove)
env.add_command(run)
env.add_command(show)
