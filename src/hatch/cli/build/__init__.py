from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Build a project')
@click.argument('location', required=False)
@click.option(
    '--target',
    '-t',
    'targets',
    multiple=True,
    help=(
        'The target to build, overriding project defaults. '
        'This may be selected multiple times e.g. `-t sdist -t wheel`'
    ),
)
@click.option(
    '--hooks-only', is_flag=True, help='Whether or not to only execute build hooks [env var: `HATCH_BUILD_HOOKS_ONLY`]'
)
@click.option(
    '--no-hooks', is_flag=True, help='Whether or not to disable build hooks [env var: `HATCH_BUILD_NO_HOOKS`]'
)
@click.option(
    '--ext',
    is_flag=True,
    help=(
        'Whether or not to only execute build hooks for distributing binary Python packages, such as '
        'compiling extensions. Equivalent to `--hooks-only -t wheel`'
    ),
)
@click.option(
    '--clean',
    '-c',
    is_flag=True,
    help='Whether or not existing artifacts should first be removed [env var: `HATCH_BUILD_CLEAN`]',
)
@click.option(
    '--clean-hooks-after',
    is_flag=True,
    help=(
        'Whether or not build hook artifacts should be removed after each build '
        '[env var: `HATCH_BUILD_CLEAN_HOOKS_AFTER`]'
    ),
)
@click.option('--clean-only', is_flag=True, hidden=True)
@click.pass_obj
def build(app: Application, location, targets, hooks_only, no_hooks, ext, clean, clean_hooks_after, clean_only):
    """Build a project."""
    app.ensure_environment_plugin_dependencies()

    from hatch.config.constants import AppEnvVars
    from hatch.utils.fs import Path
    from hatch.utils.structures import EnvVars
    from hatchling.builders.constants import EDITABLES_REQUIREMENT, BuildEnvVars
    from hatchling.builders.plugin.interface import BuilderInterface

    path = str(Path(location).resolve()) if location else None

    if ext:
        hooks_only = True
        targets = ('wheel',)
    elif not targets:
        targets = ('sdist', 'wheel')

    if app.project.metadata.build.build_backend != 'hatchling.build':
        for context in app.runner_context(['hatch-build']):
            context.add_shell_command(
                'build-sdist' if targets == ('sdist',) else 'build-wheel' if targets == ('wheel',) else 'build-all'
            )

        return

    env_vars = {}
    if no_hooks:
        env_vars[BuildEnvVars.NO_HOOKS] = 'true'

    if app.verbose:
        env_vars[AppEnvVars.VERBOSE] = str(app.verbosity)
    elif app.quiet:
        env_vars[AppEnvVars.QUIET] = str(abs(app.verbosity))

    class Builder(BuilderInterface):
        def get_version_api(self):  # noqa: PLR6301
            return {}

    with app.project.location.as_cwd(env_vars):
        environment = app.get_environment()
        if not environment.build_environment_exists():
            try:
                environment.check_compatibility()
            except Exception as e:  # noqa: BLE001
                app.abort(f'Environment `{environment.name}` is incompatible: {e}')

        for target in targets:
            target_name, _, _ = target.partition(':')
            builder = Builder(str(app.project.location))
            builder.PLUGIN_NAME = target_name

            if not clean_only:
                app.display_header(target_name)

            dependencies = list(app.project.metadata.build.requires)
            # editables is needed for "hatch build -t wheel:editable".
            dependencies.append(EDITABLES_REQUIREMENT)
            with environment.get_env_vars(), EnvVars(env_vars):
                dependencies.extend(builder.config.dependencies)

            with app.status_if(
                'Setting up build environment', condition=not environment.build_environment_exists()
            ) as status, environment.build_environment(dependencies) as build_environment:
                status.stop()

                process = environment.run_builder(
                    build_environment,
                    directory=path,
                    targets=(target,),
                    hooks_only=hooks_only,
                    no_hooks=no_hooks,
                    clean=clean,
                    clean_hooks_after=clean_hooks_after,
                    clean_only=clean_only,
                )
                if process.returncode:
                    app.abort(code=process.returncode)
