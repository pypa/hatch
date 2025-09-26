def test(hatch):
    result = hatch()

    assert result.exit_code == 0, result.output
