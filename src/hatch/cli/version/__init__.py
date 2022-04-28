import click


@click.command(short_help="View or set a project's version")
@click.argument('desired_version', required=False)
@click.pass_obj
def version(app, desired_version):
    """View or set a project's version."""
    if app.project.metadata.core.version is not None:
        if desired_version:
            app.abort('Cannot set version when it is statically defined by the `project.version` field')
        else:
            app.display_info(app.project.metadata.core.version)
            return

    from hatchling.plugin.exceptions import UnknownPluginError

    try:
        source = app.project.metadata.hatch.version.source

        version_data = source.get_version_data()
        original_version = version_data['version']

        if not desired_version:
            app.display_info(original_version)
            return

        updated_version = app.project.metadata.hatch.version.scheme.update(
            desired_version, original_version, version_data
        )
        source.set_version(updated_version, version_data)
    except UnknownPluginError:
        get_version_from_build_environment(app, desired_version)
    else:
        app.display_info(f'Old: {original_version}')
        app.display_info(f'New: {updated_version}')


def get_version_from_build_environment(app, desired_version):
    import pickle

    with app.project.location.as_cwd():
        environment = app.get_environment()

        # These are likely missing from the current environment
        dependencies = list(app.project.metadata.build.requires)

        with app.status_waiting('Setting up build environment for missing build dependencies') as status:
            with environment.build_environment(dependencies):
                status.stop()

                command = ['python', '-u', '-m', 'hatchling', 'version', '--app']
                if desired_version:
                    command.append(desired_version)

                process = app.platform.capture_process(command)

                with process:
                    for line in app.platform.stream_process_output(process):
                        indicator, _, procedure = line.partition(':')
                        if indicator != '__HATCH__':  # no cov
                            app.display_info(line, end='')
                            continue

                        method, args, kwargs = pickle.loads(bytes.fromhex(procedure.rstrip()))
                        if method == 'abort':
                            process.communicate()

                        getattr(app, method)(*args, **kwargs)

                if process.returncode:
                    app.abort(code=process.returncode)
