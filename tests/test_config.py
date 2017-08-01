import os
import shutil

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.settings import (
    DEFAULT_SETTINGS, SETTINGS_FILE, load_settings, save_settings
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


def test_update():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            new_settings = DEFAULT_SETTINGS.copy()
            new_settings.pop('email')
            new_settings['new setting'] = ''
            save_settings(new_settings)
            assert load_settings() == new_settings

            result = runner.invoke(hatch, ['config', '-u'])
            updated_settings = load_settings()

            assert result.exit_code == 0
            assert 'Settings were successfully updated.' in result.output
            assert 'Settings location: ' in result.output
            assert 'settings.json' in result.output
            assert 'email' in updated_settings
            assert 'new setting' in updated_settings


def test_update_config_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['config', '-u'])

            assert result.exit_code == 0
            assert 'Settings were successfully restored.' in result.output
            assert 'Settings location: ' in result.output
            assert 'settings.json' in result.output
            assert load_settings() == DEFAULT_SETTINGS
