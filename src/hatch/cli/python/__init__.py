import click

from hatch.cli.python.find import find
from hatch.cli.python.install import install
from hatch.cli.python.remove import remove
from hatch.cli.python.show import show
from hatch.cli.python.update import update


@click.group(short_help='Manage Python installations')
def python():
    pass


python.add_command(find)
python.add_command(install)
python.add_command(remove)
python.add_command(show)
python.add_command(update)
