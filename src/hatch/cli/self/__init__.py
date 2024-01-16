import os

import click

from hatch.cli.self.report import report

__management_command = os.environ.get('PYAPP_COMMAND_NAME', 'self')


@click.group(name=__management_command, short_help='Manage Hatch')
def self_command():
    pass


self_command.add_command(report)

if __management_command:
    from hatch.cli.self.restore import restore
    from hatch.cli.self.update import update

    self_command.add_command(restore)
    self_command.add_command(update)
