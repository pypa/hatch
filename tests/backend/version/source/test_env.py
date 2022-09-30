from itertools import product

import pytest

from hatchling.version.source.env import EnvSource

DEFAULT_PATTERN_PRODUCTS = list(product(('__version__', 'VERSION', 'version'), ('"', "'"), ('', 'v')))


def test_no_variable(isolation):
    source = EnvSource(str(isolation), {})

    with pytest.raises(ValueError, match='option `variable` must be specified'):
        source.get_version_data()


def test_variable_not_string(isolation):
    source = EnvSource(str(isolation), {'variable': 1})

    with pytest.raises(TypeError, match='option `variable` must be a string'):
        source.get_version_data()


def test_variable_not_available(isolation, monkeypatch):
    source = EnvSource(str(isolation), {'variable': 'ENV_VERSION'})

    monkeypatch.delenv('ENV_VERSION', raising=False)

    with pytest.raises(RuntimeError, match='variable `ENV_VERSION` is not set'):
        source.get_version_data()


def test_variable_contains_version(isolation, monkeypatch):
    source = EnvSource(str(isolation), {'variable': 'ENV_VERSION'})

    monkeypatch.setenv('ENV_VERSION', '0.0.1')

    assert source.get_version_data()['version'] == '0.0.1'
