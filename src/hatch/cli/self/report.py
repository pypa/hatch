from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


def get_install_source(platform_name: str) -> str:
    import os
    import sys
    import sysconfig

    from platformdirs import user_data_dir

    from hatch.utils.fs import Path

    default_source = 'pip'

    python_path = Path(sys.executable).resolve()
    parent_paths = python_path.parents

    # https://github.com/ofek/pyapp/blob/v0.13.0/src/app.rs#L27
    if Path(user_data_dir('pyapp', appauthor=False)) in parent_paths:
        return 'binary'

    # https://pypa.github.io/pipx/how-pipx-works/
    if (Path.home() / '.local' / 'pipx' / 'venvs') in parent_paths:
        return 'pipx'

    # https://packaging.python.org/en/latest/specifications/externally-managed-environments/#marking-an-interpreter-as-using-an-external-package-manager
    try:
        stdlib_path_config = sysconfig.get_path('stdlib')
    # https://docs.python.org/3/library/sysconfig.html#sysconfig.get_path
    except KeyError:
        stdlib_path_config = ''

    if (
        # This does not work on NixOS, see: https://github.com/NixOS/nixpkgs/issues/201037
        sys.prefix == sys.base_prefix
        and stdlib_path_config
        and (stdlib_path := Path(stdlib_path_config)).is_dir()
        and any(p.name == 'EXTERNALLY-MANAGED' and p.is_file() for p in stdlib_path.iterdir())
    ):
        return 'system'

    if platform_name == 'windows':
        if sys.executable.endswith('WindowsApps\\python.exe'):
            return 'Windows Store'

        # Break early because nothing after is applicable
        return default_source

    if platform_name == 'macos' and Path('/usr/local/Cellar') in parent_paths:  # no cov
        return 'Homebrew'

    # https://github.com/pyenv/pyenv/tree/v2.3.35#set-up-your-shell-environment-for-pyenv
    if Path(os.environ.get('PYENV_ROOT', '~/.pyenv')).expand() in parent_paths:
        return 'Pyenv'

    return default_source


@click.command(short_help='Generate a pre-populated GitHub issue')
@click.option('--no-open', '-n', is_flag=True, help='Show the URL instead of opening it')
@click.pass_obj
def report(app: Application, *, no_open: bool) -> None:
    """Generate a pre-populated GitHub issue."""
    import sys
    import webbrowser
    from textwrap import indent
    from urllib.parse import quote_plus

    import tomlkit

    from hatch._version import __version__
    from hatch.utils.toml import load_toml_data

    # Retain the config that would be most useful
    full_config = load_toml_data(app.config_file.read_scrubbed())
    relevant_config = {}
    for setting in ('mode', 'shell'):
        if setting in full_config:
            relevant_config[setting] = full_config[setting]

    if env_dirs := relevant_config.get('dirs', {}).get('envs'):
        relevant_config['dirs'] = {'envs': env_dirs}

    # Try to determine how Hatch was installed
    source = get_install_source(app.platform.name)

    element_padding = ' ' * 4
    body = f"""\
## Current behavior
<!-- A clear and concise description of the behavior. -->

## Expected behavior
<!-- A clear and concise description of what you expected to happen. -->

## Additional context
<!-- Add any other context about the problem here. If applicable, add screenshots to help explain. -->

## Debug

### Installation

- Source: {source}
- Version: {__version__}
- Platform: {app.platform.display_name}
- Python version:
{element_padding}```
{indent(sys.version, element_padding)}
{element_padding}```

### Configuration

```toml
{tomlkit.dumps(relevant_config).rstrip()}
```
"""

    url = f'https://github.com/pypa/hatch/issues/new?body={quote_plus(body)}'
    if no_open:
        app.display(url)
    else:
        webbrowser.open_new_tab(url)
