from __future__ import annotations

import click

from hatch.cli.check.code import code
from hatch.cli.check.fmt import fmt
from hatch.cli.check.types import types


@click.group(short_help="Check source code", invoke_without_command=True)
@click.option("--fix", is_flag=True, help="Fix issues rather than just reporting them")
@click.pass_context
def check(ctx: click.Context, *, fix: bool):
    """Check source code for issues (linting, formatting, type checking).

    When invoked without a subcommand, runs all checks (code, fmt, types).
    """
    if ctx.invoked_subcommand is not None:
        return

    ctx.invoke(code, fix=fix)
    ctx.invoke(fmt, fix=fix)
    ctx.invoke(types)


check.add_command(code)
check.add_command(fmt)
check.add_command(types)
