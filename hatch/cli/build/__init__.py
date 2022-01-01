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
    import pickle

    from hatchling.builders.plugin.interface import BuilderInterface

    from ...utils.fs import Path

    if app.project.metadata.build.build_backend != 'hatchling.build':
        app.abort('Field `build-system.build-backend` must be set to `hatchling.build`')

    backend_requirements = []
    for requirement in app.project.metadata.build.requires_complex:
        if requirement.name != 'hatchling':
            app.abort('Field `build-system.requires` must only specify `hatchling` as a requirement')

        backend_requirements.append(str(requirement))

    if not backend_requirements:
        app.abort('Field `build-system.requires` must specify `hatchling` as a requirement')

    if location:
        path = str(Path(location).resolve())
    else:
        path = None

    if ext:
        hooks_only = True
        targets = ('wheel',)
    elif not targets:
        targets = tuple(app.project.metadata.hatch.build_targets)

    if not targets:
        app.display_error('No targets defined in project configuration.')
        app.display_error('Add one or more of the following build targets to pyproject.toml:\n')

        builders = app.plugins.builder.collect(include_third_party=False)
        for target_name in sorted(builders):
            app.display_error(f'[tool.hatch.build.targets.{target_name}]')

        app.abort()

    with app.project.location.as_cwd():
        environment = app.get_environment()

        for i, target in enumerate(targets):
            # Separate targets with a blank line
            if not clean_only and i != 0:
                app.display_info()

            target_name, _, _ = target.partition(':')
            builder = BuilderInterface(str(app.project.location))
            builder.PLUGIN_NAME = target_name

            dependencies = list(backend_requirements)
            dependencies.extend(builder.config.dependencies)

            with app.status_waiting('Setting up build environment') as status:
                with environment.build_environment(dependencies) as build_environment:
                    status.stop()

                    build_process = environment.get_build_process(
                        build_environment,
                        directory=path,
                        targets=(target,),
                        hooks_only=hooks_only,
                        no_hooks=no_hooks,
                        clean=clean,
                        clean_hooks_after=clean_hooks_after,
                        clean_only=clean_only,
                    )

                    with build_process:
                        for line in app.platform.stream_process_output(build_process):
                            indicator, _, procedure = line.partition(':')
                            if indicator != '__HATCH__':  # no cov
                                app.display_info(line, end='')
                                continue

                            method, args, kwargs = pickle.loads(bytes.fromhex(procedure.rstrip()))
                            if method == 'abort':
                                build_process.communicate()

                            getattr(app, method)(*args, **kwargs)

                    if build_process.returncode:
                        app.abort(code=build_process.returncode)
