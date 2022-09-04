import warnings

import click


def check_click_supports_windows_expand_args() -> bool:
    try:
        click_version = click.__version__
    except NameError:
        # __version__ is defined since click 2.0, so if it's missing,
        # it must be some newer version.
        return True
    if not isinstance(click_version, str):
        raise ValueError(f'Click version "{click_version}" is not a string')
    if click_version.startswith('7.') or click_version in ('8.0.0', '8.0.1', '8.0.2'):
        warnings.warn(
            f'Hatch does not support Click v{click_version}. Please upgrade to Click v8.0.3 or later. To avoid '
            f'dependency issues, consider installing Hatch in an isolated environment with `pipx install hatch`.',
            DeprecationWarning,
        )
    if click_version.startswith('7.') or click_version == '8.0.0':
        # We strictly require at least 7.0, so Click can't be older than that.
        # Support for windows_expand_args was added in 8.0.1.
        return False
    else:
        # Click is 8.0.1 or later, so it supports windows_expand_args.
        return True
