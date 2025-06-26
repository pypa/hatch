import os
import importlib


def test(hatch):
    result = hatch(os.environ['PYAPP_COMMAND_NAME'])
    exit_code = 2

    click_version = importlib.metadata.version('click')
    if click_version <= '8.1.8':
        exit_code = 0

    assert result.exit_code == exit_code, result.output
