import argparse

from .build import build_command
from .dep import dep_command
from .version import version_command


def hatchling():
    parser = argparse.ArgumentParser(prog='hatchling', allow_abbrev=False)
    subparsers = parser.add_subparsers(required=True)

    defaults = {'metavar': ''}

    build_command(subparsers, defaults)
    dep_command(subparsers, defaults)
    version_command(subparsers, defaults)

    kwargs = vars(parser.parse_args())
    command = kwargs.pop('func')
    command(**kwargs)
