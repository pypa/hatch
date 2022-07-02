import click

from hatch.cli.env.create import create
from hatch.cli.env.find import find
from hatch.cli.env.prune import prune
from hatch.cli.env.remove import remove
from hatch.cli.env.run import run
from hatch.cli.env.show import show


@click.group(short_help='Manage project environments')
def env():
    pass


env.add_command(create)
env.add_command(find)
env.add_command(prune)
env.add_command(remove)
env.add_command(run)
env.add_command(show)
