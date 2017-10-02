import click

from hatch.commands import (
    build, clean, conda, config, env, grow, init, install, new, pypath,
    python, release, shed, shell, test, uninstall, update
)
from hatch.commands.utils import CONTEXT_SETTINGS


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
hatch.add_command(clean)
hatch.add_command(conda)
hatch.add_command(config)
hatch.add_command(env)
hatch.add_command(grow)
hatch.add_command(init)
hatch.add_command(install)
hatch.add_command(new)
hatch.add_command(pypath)
hatch.add_command(python)
hatch.add_command(release)
hatch.add_command(shed)
hatch.add_command(shell)
hatch.add_command(test)
hatch.add_command(uninstall)
hatch.add_command(update)
