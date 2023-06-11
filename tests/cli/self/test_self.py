import os


def test(hatch):
    result = hatch(os.environ['PYAPP_COMMAND_NAME'])

    assert result.exit_code == 0, result.output
