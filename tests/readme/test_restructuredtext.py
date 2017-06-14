from click.testing import CliRunner

from hatch.cli import hatch
from hatch.settings import DEFAULT_SETTINGS
from ..utils import temp_chdir


def test_readme_format():
    with temp_chdir() as d:
        pass
