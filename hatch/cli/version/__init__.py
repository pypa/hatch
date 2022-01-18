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

    source = app.project.config.version.source

    version_data = source.get_version_data()
    original_version = version_data['version']

    if not desired_version:
        app.display_info(original_version)
        return

    updated_version = app.project.config.version.scheme.update(desired_version, original_version, version_data)
    source.set_version(updated_version, version_data)

    app.display_info(f'Old: {original_version}')
    app.display_info(f'New: {updated_version}')
