def test_call(hatch, config_file, mocker):
    mock = mocker.patch('click.launch')
    result = hatch('config', 'explore')

    assert result.exit_code == 0, result.output
    mock.assert_called_once_with(str(config_file.path), locate=True)
