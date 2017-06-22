import os
import shutil

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.settings import (
    DEFAULT_SETTINGS, SETTINGS_FILE, load_settings, restore_settings
)
from .utils import temp_chdir


def test_show_location():
    with temp_chdir():
        runner = CliRunner()
        result = runner.invoke(hatch, ['config'])

        assert result.exit_code == 0
        assert 'Settings location: ' in result.output
        assert 'settings.json' in result.output


def test_restore():
    with temp_chdir() as d:
        saved_settings = ''
        if os.path.exists(SETTINGS_FILE):  # no cov
            saved_settings = shutil.move(SETTINGS_FILE, d)

        runner = CliRunner()
        result = runner.invoke(hatch, ['config', '--restore'])

        try:
            assert result.exit_code == 0
            assert 'Settings were successfully restored.' in result.output
            assert 'Settings location: ' in result.output
            assert 'settings.json' in result.output
            assert load_settings() == DEFAULT_SETTINGS
        finally:
            if saved_settings:  # no cov
                os.remove(SETTINGS_FILE)
                shutil.move(saved_settings, SETTINGS_FILE)
