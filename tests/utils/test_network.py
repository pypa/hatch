import re

import pytest

from hatch.config.constants import AppEnvVars
from hatch.utils.network import DEFAULT_TIMEOUT, download_file, get_timeout
from hatch.utils.structures import EnvVars


class TestGetTimeout:
    def test_default(self):
        with EnvVars(exclude=[AppEnvVars.NETWORK_TIMEOUT]):
            assert get_timeout() == DEFAULT_TIMEOUT

    @pytest.mark.parametrize("value", ["", "   "])
    def test_unset_by_empty_value(self, value):
        with EnvVars({AppEnvVars.NETWORK_TIMEOUT: value}):
            assert get_timeout() == DEFAULT_TIMEOUT

    @pytest.mark.parametrize(("value", "expected"), [("30", 30.0), ("2.5", 2.5), (" 45 ", 45.0)])
    def test_override(self, value, expected):
        with EnvVars({AppEnvVars.NETWORK_TIMEOUT: value}):
            assert get_timeout() == expected

    @pytest.mark.parametrize("value", ["foo", "10s", "1,5"])
    def test_not_a_number(self, value):
        with (
            EnvVars({AppEnvVars.NETWORK_TIMEOUT: value}),
            pytest.raises(
                ValueError, match=re.escape(f"Environment variable `{AppEnvVars.NETWORK_TIMEOUT}` must be a number")
            ),
        ):
            get_timeout()

    @pytest.mark.parametrize("value", ["0", "-1", "nan", "inf"])
    def test_not_positive(self, value):
        with (
            EnvVars({AppEnvVars.NETWORK_TIMEOUT: value}),
            pytest.raises(
                ValueError, match=re.escape(f"Environment variable `{AppEnvVars.NETWORK_TIMEOUT}` must be positive")
            ),
        ):
            get_timeout()


class TestDownloadFile:
    def test_default_timeout(self, mocker, temp_dir):
        streaming_response = mocker.patch("hatch.utils.network.streaming_response")
        streaming_response.return_value.__enter__.return_value.iter_bytes.return_value = [b"data"]

        with EnvVars(exclude=[AppEnvVars.NETWORK_TIMEOUT]):
            download_file(temp_dir / "file.txt", "https://example.com")

        assert streaming_response.call_args.kwargs["timeout"] == DEFAULT_TIMEOUT

    def test_timeout_from_env_var(self, mocker, temp_dir):
        streaming_response = mocker.patch("hatch.utils.network.streaming_response")
        streaming_response.return_value.__enter__.return_value.iter_bytes.return_value = [b"data"]

        with EnvVars({AppEnvVars.NETWORK_TIMEOUT: "45"}):
            download_file(temp_dir / "file.txt", "https://example.com")

        assert streaming_response.call_args.kwargs["timeout"] == 45.0

    def test_explicit_timeout_takes_precedence(self, mocker, temp_dir):
        streaming_response = mocker.patch("hatch.utils.network.streaming_response")
        streaming_response.return_value.__enter__.return_value.iter_bytes.return_value = [b"data"]

        with EnvVars({AppEnvVars.NETWORK_TIMEOUT: "45"}):
            download_file(temp_dir / "file.txt", "https://example.com", timeout=5)

        assert streaming_response.call_args.kwargs["timeout"] == 5
