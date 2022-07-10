import os

from hatch.config.constants import ConfigEnvVars
from hatch.config.user import ConfigFile
from hatch.utils.structures import EnvVars


class TestFreshInstallation:
    INSTALL_MESSAGE = """\
No config file found, creating one with default settings now...
Success! Please see `hatch config`.
"""

    def test_config_file_creation_default(self, hatch):
        with EnvVars():
            os.environ.pop(ConfigEnvVars.CONFIG, None)
            with ConfigFile.get_default_location().temp_hide():
                result = hatch()
                assert self.INSTALL_MESSAGE not in result.output

    def test_config_file_creation_verbose(self, hatch):
        with EnvVars():
            os.environ.pop(ConfigEnvVars.CONFIG, None)
            with ConfigFile.get_default_location().temp_hide():
                result = hatch('-v')
                assert self.INSTALL_MESSAGE in result.output

                result = hatch('-v')
                assert self.INSTALL_MESSAGE not in result.output


def test_no_subcommand_shows_help(hatch):
    assert hatch().output == hatch('--help').output


def test_no_config_file(hatch, config_file):
    config_file.path.remove()
    result = hatch()

    assert result.exit_code == 1
    assert result.output == f'The selected config file `{str(config_file.path)}` does not exist.\n'
