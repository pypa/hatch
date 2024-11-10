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
    help='Allow an explicit downgrading version to be given',
)
@click.pass_obj
def version(app: Application, *, desired_version: str | None, force: bool):
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
            data['project']['version'] = updated_version  # type: ignore[index]
            file.write(data)

            app.display_info(f'Old: {original_version}')
            app.display_info(f'New: {updated_version}')
            return

        app.display(original_version)
        return

    from hatch.config.constants import VersionEnvVars
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
        else:
            from hatch.utils.runner import ExecutionContext

            app.ensure_environment_plugin_dependencies()
            app.project.prepare_build_environment()

            context = ExecutionContext(app.project.build_env)
            command = ['python', '-u', '-m', 'hatchling', 'version']
            if desired_version:
                command.append(desired_version)
                if force:
                    context.env_vars[VersionEnvVars.VALIDATE_BUMP] = 'false'

            context.add_shell_command(command)
            app.execute_context(context)
