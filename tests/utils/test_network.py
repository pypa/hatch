from hatch.config.constants import NetworkEnvVars
from hatch.utils.network import DEFAULT_TIMEOUT, get_default_timeout


def test_default_timeout():
    assert get_default_timeout() == DEFAULT_TIMEOUT


def test_default_timeout_env_var(monkeypatch):
    monkeypatch.setenv(NetworkEnvVars.TIMEOUT, "42.5")

    assert get_default_timeout() == 42.5
