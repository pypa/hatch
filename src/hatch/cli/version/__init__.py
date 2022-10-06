import click


@click.command(short_help="View or set a project's version")
@click.argument('desired_version', required=False)
@click.pass_obj
def version(app, desired_version):
    """View or set a project's version."""
    if 'version' in app.project.metadata.config.get('project', {}):
        if desired_version:
            app.abort('Cannot set version when it is statically defined by the `project.version` field')
        else:
            app.display_always(app.project.metadata.core.version)
            return

    from hatchling.dep.core import dependencies_in_sync

    with app.project.location.as_cwd():
        dynamic_version = 'version' in app.project.metadata.dynamic
        if not dynamic_version or dependencies_in_sync(app.project.metadata.build.requires_complex):
            source = app.project.metadata.hatch.version.source

            version_data = source.get_version_data()
            original_version = version_data['version']

            if not desired_version:
                app.display_always(original_version)
                return

            updated_version = app.project.metadata.hatch.version.scheme.update(
                desired_version, original_version, version_data
            )
            source.set_version(updated_version, version_data)

            app.display_info(f'Old: {original_version}')
            app.display_info(f'New: {updated_version}')
        else:
            environment = app.get_environment()
            try:
                environment.check_compatibility()
            except Exception as e:
                app.abort(f'Environment `{environment.name}` is incompatible: {e}')

            with app.status_waiting(
                'Setting up build environment for missing build dependencies',
                condition=not environment.build_environment_exists(),
            ) as status:
                with environment.build_environment(app.project.metadata.build.requires):
                    status.stop()

                    command = ['python', '-u', '-m', 'hatchling', 'version', '--app']
                    if desired_version:
                        command.append(desired_version)

                    process = app.platform.capture_process(command)
                    app.attach_builder(process)
