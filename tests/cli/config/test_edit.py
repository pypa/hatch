def test_call(hatch, config_file, mocker):
    mock = mocker.patch('click.edit')
    result = hatch('config', 'edit')

    assert result.exit_code == 0, result.output
    mock.assert_called_once_with(filename=str(config_file.path))
