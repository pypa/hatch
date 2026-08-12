from __future__ import annotations

import click

from hatch.cli.lazy import LazyGroup

_LAZY_SUBCOMMANDS = {
    "code": "hatch.cli.check.code:code",
    "fmt": "hatch.cli.check.fmt:fmt",
    "types": "hatch.cli.check.types:types",
}

@click.group(
    cls=LazyGroup,
    lazy_subcommands=_LAZY_SUBCOMMANDS,
    context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 120},
    invoke_without_command=True,
    short_help="Check source code",
)

@click.option("--fix", is_flag=True, help="Fix issues rather than just reporting them")
@click.pass_context
def check(ctx: click.Context, *, fix: bool):
    """Check source code for issues (linting, formatting, type checking).

    When invoked without a subcommand, runs all checks (code, fmt, types).
    """
    if ctx.invoked_subcommand is not None:
        return

    from hatch.cli.check.code import code
    from hatch.cli.check.fmt import fmt
    from hatch.cli.check.types import types

    ctx.invoke(code, fix=fix)
    ctx.invoke(fmt, fix=fix)
    ctx.invoke(types)

