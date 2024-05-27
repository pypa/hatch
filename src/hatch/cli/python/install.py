from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


def ensure_path_public(path: str, shells: list[str]) -> bool:
    import userpath

    if userpath.in_current_path(path) or userpath.in_new_path(path, shells):
        return True

    userpath.append(path, shells=shells)
    return False


@click.command(short_help='Install Python distributions')
@click.argument('names', required=True, nargs=-1)
@click.option('--private', is_flag=True, help='Do not add distributions to the user PATH')
@click.option('--update', '-u', is_flag=True, help='Update existing installations')
@click.option(
    '--dir', '-d', 'directory', help='The directory in which to install distributions, overriding configuration'
)
@click.pass_obj
def install(app: Application, *, names: tuple[str, ...], private: bool, update: bool, directory: str | None):
    """
    Install Python distributions.

    You may select `all` to install all compatible distributions:

    \b
    ```
    hatch python install all
    ```

    You can set custom sources for distributions by setting the `HATCH_PYTHON_SOURCE_<NAME>` environment variable
    where `<NAME>` is the uppercased version of the distribution name with periods replaced by underscores e.g.
    `HATCH_PYTHON_SOURCE_PYPY3_10`.
    """
    from hatch.errors import PythonDistributionResolutionError, PythonDistributionUnknownError
    from hatch.python.distributions import ORDERED_DISTRIBUTIONS
    from hatch.python.resolve import get_distribution

    shells = []
    if not private and not app.platform.windows:
        shell_name, _ = app.shell_data
        shells.append(shell_name)

    manager = app.get_python_manager(directory)
    installed = manager.get_installed()
    selection = ORDERED_DISTRIBUTIONS if 'all' in names else names
    unknown = []
    compatible = []
    incompatible = []
    for name in selection:
        if name in installed:
            compatible.append(name)
            continue

        try:
            get_distribution(name)
        except PythonDistributionUnknownError:
            unknown.append(name)
        except PythonDistributionResolutionError:
            incompatible.append(name)
        else:
            compatible.append(name)

    if unknown:
        app.abort(f'Unknown distributions: {", ".join(unknown)}')
    elif incompatible and (not compatible or 'all' not in names):
        app.abort(f'Incompatible distributions: {", ".join(incompatible)}')

    directories_made_public = []
    for name in compatible:
        needs_update = False
        if name in installed:
            installed_dist = installed[name]
            needs_update = installed_dist.needs_update()
            if not needs_update:
                app.display_warning(f'The latest version is already installed: {installed_dist.version}')
                continue

            if not (update or app.confirm(f'Update {name}?')):
                app.abort(f'Distribution is already installed: {name}')

        with app.status(f'{"Updating" if needs_update else "Installing"} {name}'):
            dist = manager.install(name)
            if not private:
                python_directory = str(dist.python_path.parent)
                if not ensure_path_public(python_directory, shells=shells):
                    directories_made_public.append(python_directory)

        app.display_success(f'{"Updated" if needs_update else "Installed"} {name} @ {dist.path}')

    if directories_made_public:
        multiple = len(directories_made_public) > 1
        app.display(
            f'\nThe following director{"ies" if multiple else "y"} ha{"ve" if multiple else "s"} '
            f'been added to your PATH (pending a shell restart):\n'
        )
        for public_directory in directories_made_public:
            app.display(public_directory)
