import click


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
def build(app, location, targets, hooks_only, no_hooks, ext, clean, clean_hooks_after, clean_only):
    """Build a project."""
    from hatchling.builders.constants import BuildEnvVars
    from hatchling.builders.plugin.interface import BuilderInterface

    from hatch.utils.fs import Path
    from hatch.utils.structures import EnvVars

    if app.project.metadata.build.build_backend != 'hatchling.build':
        app.abort('Field `build-system.build-backend` must be set to `hatchling.build`')

    for requirement in app.project.metadata.build.requires_complex:
        if requirement.name == 'hatchling':
            break
    else:
        app.abort('Field `build-system.requires` must specify `hatchling` as a requirement')

    if location:
        path = str(Path(location).resolve())
    else:
        path = None

    if ext:
        hooks_only = True
        targets = ('wheel',)
    elif not targets:
        targets = ('sdist', 'wheel')

    env_vars = {}
    if no_hooks:
        env_vars[BuildEnvVars.NO_HOOKS] = 'true'

    class Builder(BuilderInterface):
        def get_version_api(self):
            return {}

    with app.project.location.as_cwd(env_vars):
        environment = app.get_environment()
        try:
            environment.check_compatibility()
        except Exception as e:
            app.abort(f'Environment `{environment.name}` is incompatible: {e}')

        for i, target in enumerate(targets):
            # Separate targets with a blank line
            if not clean_only and i != 0:
                app.display_info()

            target_name, _, _ = target.partition(':')
            builder = Builder(str(app.project.location))
            builder.PLUGIN_NAME = target_name

            dependencies = list(app.project.metadata.build.requires)
            with environment.get_env_vars(), EnvVars(env_vars):
                dependencies.extend(builder.config.dependencies)

            with app.status_waiting(
                'Setting up build environment', condition=not environment.build_environment_exists()
            ) as status:
                with environment.build_environment(dependencies) as build_environment:
                    status.stop()

                    process = environment.get_build_process(
                        build_environment,
                        directory=path,
                        targets=(target,),
                        hooks_only=hooks_only,
                        no_hooks=no_hooks,
                        clean=clean,
                        clean_hooks_after=clean_hooks_after,
                        clean_only=clean_only,
                    )
                    app.attach_builder(process)
