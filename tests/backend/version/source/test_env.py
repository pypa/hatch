import pytest

from hatch.utils.structures import EnvVars
from hatchling.version.source.env import EnvSource


def test_no_variable(isolation):
    source = EnvSource(str(isolation), {})

    with pytest.raises(ValueError, match='option `variable` must be specified'):
        source.get_version_data()


def test_variable_not_string(isolation):
    source = EnvSource(str(isolation), {'variable': 1})

    with pytest.raises(TypeError, match='option `variable` must be a string'):
        source.get_version_data()


def test_variable_not_available(isolation):
    source = EnvSource(str(isolation), {'variable': 'ENV_VERSION'})

    with EnvVars(exclude=['ENV_VERSION']), pytest.raises(
        RuntimeError, match='environment variable `ENV_VERSION` is not set'
    ):
        source.get_version_data()


def test_variable_contains_version(isolation):
    source = EnvSource(str(isolation), {'variable': 'ENV_VERSION'})

    with EnvVars({'ENV_VERSION': '0.0.1'}):
        assert source.get_version_data()['version'] == '0.0.1'
