from hatch.config.model import BaseConfig


def test_standard(hatch, config_file):
    config_file.model.project = 'foo'
    config_file.save()

    result = hatch('config', 'restore')

    assert result.exit_code == 0, result.output
    assert result.output == 'Settings were successfully restored.\n'

    config_file.load()
    assert config_file.model.project == ''


def test_allow_invalid_config(hatch, config_file, helpers):
    # This gives us a usable but also broken config
    config_file.model = BaseConfig()
    config_file.save()

    result = hatch('config', 'restore')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Settings were successfully restored.
        """
    )
