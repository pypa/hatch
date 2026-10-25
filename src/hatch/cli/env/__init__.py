import click

from hatch.cli.lazy import LazyGroup

_LAZY_SUBCOMMANDS = {
    "create": "hatch.cli.env.create:create",
    "find": "hatch.cli.env.find:find",
    "lock": "hatch.cli.env.lock:lock",
    "prune": "hatch.cli.env.prune:prune",
    "remove": "hatch.cli.env.remove:remove",
    "run": "hatch.cli.env.run:run",
    "show": "hatch.cli.env.show:show",
}


@click.group(
    cls=LazyGroup,
    lazy_subcommands=_LAZY_SUBCOMMANDS,
    context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 120},
    invoke_without_command=True,
)
def env():
    pass
