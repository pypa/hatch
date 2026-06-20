import os


def test(hatch):
    result = hatch(os.environ["PYAPP_COMMAND_NAME"], "-h")

    assert result.exit_code == 0, result.output
