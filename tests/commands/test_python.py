from click.testing import CliRunner

from hatch.cli import hatch
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, load_settings, restore_settings,
    save_settings
)
from hatch.utils import temp_chdir, temp_move_path


def test_config_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['python', 'name', 'path'])

        assert result.exit_code == 1
        assert 'Unable to locate config file. Try `hatch config --restore`.' in result.output


def test_success():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            restore_settings()
            result = runner.invoke(hatch, ['python', 'name', 'path'])
            settings = load_settings()

            assert settings['pythons']['name'] == 'path'

        assert result.exit_code == 0
        assert 'Successfully saved Python `name` located at `path`.' in result.output


def test_success_missing_key():
    with temp_chdir() as d:
        runner = CliRunner()

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings.pop('pythons')
            save_settings(settings)
            result = runner.invoke(hatch, ['python', 'name', 'path'])
            settings = load_settings()

            assert settings['pythons']['name'] == 'path'
            assert list(settings.keys())[-1] != 'pythons'

        assert result.exit_code == 0
        assert 'Settings were successfully updated to include `pythons` entry.' in result.output
        assert 'Successfully saved Python `name` located at `path`.' in result.output
