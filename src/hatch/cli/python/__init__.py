import click

from hatch.cli.lazy import LazyGroup

_LAZY_SUBCOMMANDS = {
    "find": "hatch.cli.python.find:find",
    "install": "hatch.cli.python.install:install",
    "update": "hatch.cli.python.update:update",
    "remove": "hatch.cli.python.remove:remove",
    "show": "hatch.cli.python.show:show",
}

@click.group(
    cls=LazyGroup,
    lazy_subcommands=_LAZY_SUBCOMMANDS,
    context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 120},
    invoke_without_command=True,
    short_help="Manage Python installations",
)
def python():
    pass
