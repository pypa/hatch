import pytest

from hatch.config.constants import AppEnvVars
from hatch.utils.network import DEFAULT_TIMEOUT, get_default_timeout


def test_get_default_timeout_default(monkeypatch):
    monkeypatch.delenv(AppEnvVars.NETWORK_TIMEOUT, raising=False)

    assert get_default_timeout() == DEFAULT_TIMEOUT


def test_get_default_timeout_env_var(monkeypatch):
    monkeypatch.setenv(AppEnvVars.NETWORK_TIMEOUT, "30.5")

    assert get_default_timeout() == 30.5


@pytest.mark.parametrize("value", ["0", "-1", "foo", "nan", "inf"])
def test_get_default_timeout_invalid(monkeypatch, value):
    monkeypatch.setenv(AppEnvVars.NETWORK_TIMEOUT, value)

    with pytest.raises(
        ValueError, match=f"Environment variable `{AppEnvVars.NETWORK_TIMEOUT}` must be a positive number"
    ):
        get_default_timeout()
