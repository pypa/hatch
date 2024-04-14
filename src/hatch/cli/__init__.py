import os

import click

from hatch._version import __version__
from hatch.cli.application import Application
from hatch.cli.build import build
from hatch.cli.clean import clean
from hatch.cli.config import config
from hatch.cli.dep import dep
from hatch.cli.env import env
from hatch.cli.fmt import fmt
from hatch.cli.new import new
from hatch.cli.project import project
from hatch.cli.publish import publish
from hatch.cli.python import python
from hatch.cli.run import run
from hatch.cli.self import self_command
from hatch.cli.shell import shell
from hatch.cli.status import status
from hatch.cli.test import test
from hatch.cli.version import version
from hatch.config.constants import AppEnvVars, ConfigEnvVars
from hatch.project.core import Project
from hatch.utils.ci import running_in_ci
from hatch.utils.fs import Path


@click.group(
    context_settings={'help_option_names': ['-h', '--help'], 'max_content_width': 120}, invoke_without_command=True
)
@click.option(
    '--env',
    '-e',
    'env_name',
    envvar=AppEnvVars.ENV,
    default='default',
    help='The name of the environment to use [env var: `HATCH_ENV`]',
)
@click.option(
    '--project',
    '-p',
    envvar=ConfigEnvVars.PROJECT,
    help='The name of the project to work on [env var: `HATCH_PROJECT`]',
)
@click.option(
    '--verbose',
    '-v',
    envvar=AppEnvVars.VERBOSE,
    count=True,
    help='Increase verbosity (can be used additively) [env var: `HATCH_VERBOSE`]',
)
@click.option(
    '--quiet',
    '-q',
    envvar=AppEnvVars.QUIET,
    count=True,
    help='Decrease verbosity (can be used additively) [env var: `HATCH_QUIET`]',
)
@click.option(
    '--color/--no-color',
    default=None,
    help='Whether or not to display colored output (default is auto-detection) [env vars: `FORCE_COLOR`/`NO_COLOR`]',
)
@click.option(
    '--interactive/--no-interactive',
    envvar=AppEnvVars.INTERACTIVE,
    default=None,
    help=(
        'Whether or not to allow features like prompts and progress bars (default is auto-detection) '
        '[env var: `HATCH_INTERACTIVE`]'
    ),
)
@click.option(
    '--data-dir',
    envvar=ConfigEnvVars.DATA,
    help='The path to a custom directory used to persist data [env var: `HATCH_DATA_DIR`]',
)
@click.option(
    '--cache-dir',
    envvar=ConfigEnvVars.CACHE,
    help='The path to a custom directory used to cache data [env var: `HATCH_CACHE_DIR`]',
)
@click.option(
    '--config',
    'config_file',
    envvar=ConfigEnvVars.CONFIG,
    help='The path to a custom config file to use [env var: `HATCH_CONFIG`]',
)
@click.version_option(version=__version__, prog_name='Hatch')
@click.pass_context
def hatch(ctx: click.Context, env_name, project, verbose, quiet, color, interactive, data_dir, cache_dir, config_file):
    """
    \b
     _   _       _       _
    | | | |     | |     | |
    | |_| | __ _| |_ ___| |__
    |  _  |/ _` | __/ __| '_ \\
    | | | | (_| | || (__| | | |
    \\_| |_/\\__,_|\\__\\___|_| |_|
    """
    if color is None:
        if os.environ.get(AppEnvVars.NO_COLOR) == '1':
            color = False
        elif os.environ.get(AppEnvVars.FORCE_COLOR) == '1':
            color = True

    if interactive is None and running_in_ci():
        interactive = False

    app = Application(ctx.exit, verbosity=verbose - quiet, enable_color=color, interactive=interactive)

    app.env_active = os.environ.get(AppEnvVars.ENV_ACTIVE)
    if (
        app.env_active
        and (param_source := ctx.get_parameter_source('env_name')) is not None
        and param_source.name == 'DEFAULT'
    ):
        app.env = app.env_active
    else:
        app.env = env_name

    if config_file:
        app.config_file.path = Path(config_file).resolve()
        if not app.config_file.path.is_file():
            app.abort(f'The selected config file `{app.config_file.path}` does not exist.')
    elif not app.config_file.path.is_file():
        if app.verbose:
            app.display_waiting('No config file found, creating one with default settings now...')

        try:
            app.config_file.restore()
            if app.verbose:
                app.display_success('Success! Please see `hatch config`.')
        except OSError:  # no cov
            app.abort(
                f'Unable to create config file located at `{app.config_file.path}`. Please check your permissions.'
            )

    if not ctx.invoked_subcommand:
        app.display_info(ctx.get_help())
        return

    # Persist app data for sub-commands
    ctx.obj = app

    try:
        app.config_file.load()
    except OSError as e:  # no cov
        app.abort(f'Error loading configuration: {e}')

    app.config.terminal.styles.parse_fields()
    errors = app.initialize_styles(app.config.terminal.styles.raw_data)
    if errors and color is not False and not app.quiet:  # no cov
        for error in errors:
            app.display_warning(error)

    app.data_dir = Path(data_dir or app.config.dirs.data).expand()
    app.cache_dir = Path(cache_dir or app.config.dirs.cache).expand()

    if project:
        app.project = Project.from_config(app.config, project)
        if app.project is None or app.project.root is None:
            app.abort(f'Unable to locate project {project}')

        return

    app.project = Project(Path.cwd())

    if app.config.mode == 'local':
        return

    # The following logic is mostly duplicated for each branch so coverage can be asserted
    if app.config.mode == 'project':
        if not app.config.project:
            app.display_warning('Mode is set to `project` but no project is set, defaulting to the current directory')
            return

        possible_project = Project.from_config(app.config, app.config.project)
        if possible_project is None:
            app.display_warning(f'Unable to locate project {app.config.project}, defaulting to the current directory')
        else:
            app.project = possible_project

        return

    if app.config.mode == 'aware' and app.project.root is None:
        if not app.config.project:
            app.display_warning('Mode is set to `aware` but no project is set, defaulting to the current directory')
            return

        possible_project = Project.from_config(app.config, app.config.project)
        if possible_project is None:
            app.display_warning(f'Unable to locate project {app.config.project}, defaulting to the current directory')
        else:
            app.project = possible_project

        return


hatch.add_command(build)
hatch.add_command(clean)
hatch.add_command(config)
hatch.add_command(dep)
hatch.add_command(env)
hatch.add_command(fmt)
hatch.add_command(new)
hatch.add_command(project)
hatch.add_command(publish)
hatch.add_command(python)
hatch.add_command(run)
hatch.add_command(self_command)
hatch.add_command(shell)
hatch.add_command(status)
hatch.add_command(test)
hatch.add_command(version)


def main():  # no cov
    try:
        hatch(prog_name='hatch', windows_expand_args=False)
    except Exception:  # noqa: BLE001
        import sys

        from rich.console import Console

        console = Console()
        hatch_debug = os.getenv('HATCH_DEBUG') in {'1', 'true'}
        console.print_exception(suppress=[click], show_locals=hatch_debug)
        sys.exit(1)
