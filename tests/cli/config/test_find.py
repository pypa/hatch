import os

import pytest

from hatch.config.constants import ConfigEnvVars


def test_copy(hatch, config_file, mocker):
    mock = mocker.patch('pyperclip.copy')
    result = hatch('config', 'find', '-c')

    assert result.exit_code == 0, result.output
    mock.assert_called_once_with(str(config_file.path))


def test_pipe_to_editor(hatch, config_file):
    config_file.path = config_file.path.parent / 'a space' / 'config.toml'
    config_file.path.ensure_parent_dir_exists()
    config_file.restore()
    os.environ[ConfigEnvVars.CONFIG] = str(config_file.path)

    result = hatch('config', 'find')

    assert result.exit_code == 0, result.output
    assert result.output == f'"{str(config_file.path)}"\n'


def test_standard(hatch, config_file):
    config_path = str(config_file.path)
    if ' ' in config_path:  # no cov
        pytest.xfail('Path to system temporary directory contains spaces')

    result = hatch('config', 'find')

    assert result.exit_code == 0, result.output
    assert result.output == f'{config_path}\n'
