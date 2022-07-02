import click


@click.command(short_help='Remove build artifacts')
@click.argument('location', required=False)
@click.option(
    '--target',
    '-t',
    'targets',
    multiple=True,
    help=(
        'The target with which to remove artifacts, overriding project defaults. '
        'This may be selected multiple times e.g. `-t sdist -t wheel`'
    ),
)
@click.option(
    '--hooks-only',
    is_flag=True,
    help='Whether or not to only remove artifacts from build hooks [env var: `HATCH_BUILD_HOOKS_ONLY`]',
)
@click.option(
    '--no-hooks',
    is_flag=True,
    help='Whether or not to ignore artifacts from build hooks [env var: `HATCH_BUILD_NO_HOOKS`]',
)
@click.option(
    '--ext',
    is_flag=True,
    help=(
        'Whether or not to only remove artifacts from build hooks for distributing binary Python packages, such as '
        'compiled extensions. Equivalent to `--hooks-only -t wheel`'
    ),
)
@click.pass_context
def clean(ctx, location, targets, hooks_only, no_hooks, ext):
    """Remove build artifacts."""
    from hatch.cli.build import build

    ctx.invoke(
        build, clean_only=True, location=location, targets=targets, hooks_only=hooks_only, no_hooks=no_hooks, ext=ext
    )
