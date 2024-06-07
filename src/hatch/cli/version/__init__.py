from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help="View or set a project's version")
@click.argument('desired_version', required=False)
@click.pass_obj
def version(app: Application, desired_version: str | None):
    """View or set a project's version."""
    if app.project.root is None:
        if app.project.chosen_name is None:
            app.abort('No project detected')
        else:
            app.abort(f'Project {app.project.chosen_name} (not a project)')

    if 'version' in app.project.metadata.config.get('project', {}):
        original_version = app.project.metadata.config['project']['version']

        if desired_version:
            import tomlkit.toml_file

            from hatchling.version.scheme.standard import StandardScheme

            updated_version = StandardScheme(str(app.project.location), {}).update(
                desired_version, original_version, {}
            )

            # keep toml style
            file = tomlkit.toml_file.TOMLFile(app.project.location.joinpath('pyproject.toml'))

            data = file.read()
            data['project']['version'] = updated_version  # type: ignore
            file.write(data)

            app.display_info(f'Old: {original_version}')
            app.display_info(f'New: {updated_version}')
            return

        app.display(original_version)
        return

    from hatchling.dep.core import dependencies_in_sync

    with app.project.location.as_cwd():
        if not (
            'version' in app.project.metadata.dynamic or app.project.metadata.hatch.metadata.hook_config
        ) or dependencies_in_sync(app.project.metadata.build.requires_complex):
            source = app.project.metadata.hatch.version.source

            version_data = source.get_version_data()
            original_version = version_data['version']

            if not desired_version:
                app.display(original_version)
                return

            updated_version = app.project.metadata.hatch.version.scheme.update(
                desired_version, original_version, version_data
            )
            source.set_version(updated_version, version_data)

            app.display_info(f'Old: {original_version}')
            app.display_info(f'New: {updated_version}')
        else:
            app.ensure_environment_plugin_dependencies()

            environment = app.get_environment()
            build_environment_exists = environment.build_environment_exists()
            if not build_environment_exists:
                try:
                    environment.check_compatibility()
                except Exception as e:  # noqa: BLE001
                    app.abort(f'Environment `{environment.name}` is incompatible: {e}')

            with app.status_if(
                'Setting up build environment for missing dependencies',
                condition=not build_environment_exists,
            ) as status, environment.build_environment(app.project.metadata.build.requires):
                status.stop()

                command = ['python', '-u', '-m', 'hatchling', 'version']
                if desired_version:
                    command.append(desired_version)

                process = app.platform.run_command(command)
                if process.returncode:
                    app.abort(code=process.returncode)
