import argparse
import sys

from .build import build_command
from .dep import dep_command


def hatchling():
    # TODO: remove when we drop Python 2
    if sys.version_info[0] < 3:  # no cov
        parser = argparse.ArgumentParser(prog='hatchling')
        subparsers = parser.add_subparsers()
    else:
        parser = argparse.ArgumentParser(prog='hatchling', allow_abbrev=False)
        subparsers = parser.add_subparsers(required=True)

    defaults = {'metavar': ''}

    build_command(subparsers, defaults)
    dep_command(subparsers, defaults)

    kwargs = vars(parser.parse_args())
    command = kwargs.pop('func')
    command(**kwargs)
