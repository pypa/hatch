def test(hatch, config_file, helpers):
    result = hatch('config', 'find')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {config_file.path}
        """
    )
