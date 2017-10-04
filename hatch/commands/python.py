import sys

import click
import userpath
from appdirs import user_data_dir

from hatch.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_success, echo_warning
)
from hatch.settings import copy_default_settings, load_settings, save_settings
from hatch.utils import conda_available


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Manages Python installations')
@click.argument('name')
@click.argument('path')
def python():  # no cov
    if not conda_available():
        echo_failure('Conda is unavailable. You can install it by doing `hatch conda`.')
        sys.exit(1)
