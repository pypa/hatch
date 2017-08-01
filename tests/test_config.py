import os
import shutil

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.settings import (
    DEFAULT_SETTINGS, SETTINGS_FILE, load_settings
)
from hatch.utils import temp_chdir, temp_move_path


def test_show_location():
    with temp_chdir():
        runner = CliRunner()
        result = runner.invoke(hatch, ['config'])

        assert result.exit_code == 0
        assert 'Settings location: ' in result.output
        assert 'settings.json' in result.output


def test_restore():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['config', '--restore'])

            assert result.exit_code == 0
            assert 'Settings were successfully restored.' in result.output
            assert 'Settings location: ' in result.output
            assert 'settings.json' in result.output
            assert load_settings() == DEFAULT_SETTINGS
