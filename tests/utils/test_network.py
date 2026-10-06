# SPDX-FileCopyrightText: 2022-present Ofek Lev <oss@ofek.dev>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from hatch.utils.network import DEFAULT_TIMEOUT, TIMEOUT_ENV_VAR, get_timeout


class TestGetTimeout:
    def test_default(self, monkeypatch):
        monkeypatch.delenv(TIMEOUT_ENV_VAR, raising=False)

        assert get_timeout() == DEFAULT_TIMEOUT

    def test_empty_value_uses_default(self, monkeypatch):
        monkeypatch.setenv(TIMEOUT_ENV_VAR, "   ")

        assert get_timeout() == DEFAULT_TIMEOUT

    @pytest.mark.parametrize(("value", "expected"), [("30", 30.0), ("0.5", 0.5), (" 45 ", 45.0)])
    def test_override(self, monkeypatch, value, expected):
        monkeypatch.setenv(TIMEOUT_ENV_VAR, value)

        assert get_timeout() == expected

    def test_not_a_number(self, monkeypatch):
        monkeypatch.setenv(TIMEOUT_ENV_VAR, "soon")

        with pytest.raises(
            ValueError, match=f"Invalid value for `{TIMEOUT_ENV_VAR}`, expected a number of seconds: soon"
        ):
            get_timeout()

    @pytest.mark.parametrize("value", ["0", "-1"])
    def test_not_positive(self, monkeypatch, value):
        monkeypatch.setenv(TIMEOUT_ENV_VAR, value)

        with pytest.raises(
            ValueError,
            match=f"Invalid value for `{TIMEOUT_ENV_VAR}`, expected a positive number of seconds: {value}",
        ):
            get_timeout()
