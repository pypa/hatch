from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help="View or set a project's version")
@click.argument('desired_version', required=False)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    default=False,
    show_default=True,
    help='Allow an explicit downgrading version to be given',
)
@click.pass_obj
def version(app: Application, desired_version: str | None, *, force: bool):
    """View or set a project's version."""
    if app.project.root is None:
        if app.project.chosen_name is None:
            app.abort('No project detected')
        else:
            app.abort(f'Project {app.project.chosen_name} (not a project)')

    if 'version' in app.project.metadata.config.get('project', {}):
        if desired_version:
            app.abort('Cannot set version when it is statically defined by the `project.version` field')
        else:
            app.display(app.project.metadata.config['project']['version'])
            return

    from hatch.project.constants import BUILD_BACKEND

    with app.project.location.as_cwd():
        if app.project.metadata.build.build_backend != BUILD_BACKEND:
            if desired_version:
                app.abort('The version can only be set when Hatchling is the build backend')

            app.ensure_environment_plugin_dependencies()
            app.project.prepare_build_environment()

            with app.project.location.as_cwd(), app.project.build_env.get_env_vars():
                project_metadata = app.project.build_frontend.get_core_metadata()

            app.display(project_metadata['version'])
        elif 'version' not in app.project.metadata.dynamic:
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
            from hatch.utils.runner import ExecutionContext

            app.ensure_environment_plugin_dependencies()
            app.project.prepare_build_environment()

            command = ['python', '-u', '-m', 'hatchling', 'version']
            if desired_version:
                if force:
                    command.append('--force')
                command.append(desired_version)

            context = ExecutionContext(app.project.build_env)
            context.add_shell_command(command)
            app.execute_context(context)
