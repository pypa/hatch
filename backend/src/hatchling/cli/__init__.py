import argparse

from hatchling.cli.build import build_command
from hatchling.cli.dep import dep_command
from hatchling.cli.metadata import metadata_command
from hatchling.cli.version import version_command


def hatchling() -> int:
    parser = argparse.ArgumentParser(prog='hatchling', allow_abbrev=False)
    subparsers = parser.add_subparsers()

    defaults = {'metavar': ''}

    build_command(subparsers, defaults)
    dep_command(subparsers, defaults)
    metadata_command(subparsers, defaults)
    version_command(subparsers, defaults)

    # Parse known arguments
    kwargs, extras = parser.parse_known_args()
    
    # Extras can exist to be detected in custom hooks and plugins,
    # but they must be after a '--' separator
    if extras and extras[0] != "--":
        parser.print_help()
        return 1

    # Wrap the parsed arguments in a dictionary
    kwargs = vars(kwargs)

    try:
        command = kwargs.pop('func')
    except KeyError:
        parser.print_help()
    else:
        command(**kwargs)

    return 0
