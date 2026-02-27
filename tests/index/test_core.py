import json
import platform

import httpx
import pytest

from hatch._version import __version__
from hatch.index.core import PackageIndex
from hatch.utils.linehaul import get_linehaul_component


class TestRepo:
    def test_normalization(self):
        index = PackageIndex("Https://Foo.Internal/z/../a/b/")

        assert index.repo == "https://foo.internal/a/b/"


class TestURLs:
    @pytest.mark.parametrize(
        ("repo_url", "expected_url"),
        [
            pytest.param("https://upload.pypi.org/legacy/", "https://pypi.org/simple/", id="PyPI main"),
            pytest.param("https://test.pypi.org/legacy/", "https://test.pypi.org/simple/", id="PyPI test"),
            pytest.param("https://foo.internal/a/b/", "https://foo.internal/a/b/%2Bsimple/", id="default"),
        ],
    )
    def test_simple(self, repo_url, expected_url):
        index = PackageIndex(repo_url)

        assert str(index.urls.simple) == expected_url

    @pytest.mark.parametrize(
        ("repo_url", "expected_url"),
        [
            pytest.param("https://upload.pypi.org/legacy/", "https://pypi.org/project/", id="PyPI main"),
            pytest.param("https://test.pypi.org/legacy/", "https://test.pypi.org/project/", id="PyPI test"),
            pytest.param("https://foo.internal/a/b/", "https://foo.internal/a/b/", id="default"),
        ],
    )
    def test_project(self, repo_url, expected_url):
        index = PackageIndex(repo_url)

        assert str(index.urls.project) == expected_url


class TestTLS:
    def test_default(self, mocker):
        mock = mocker.patch("httpx._transports.default.create_ssl_context")
        index = PackageIndex("https://foo.internal/a/b/")
        _ = index.client

        mock.assert_called_once_with(verify=True, cert=None, trust_env=True)

    def test_ca_cert(self, mocker):
        mock = mocker.patch("httpx._transports.default.create_ssl_context")
        index = PackageIndex("https://foo.internal/a/b/", ca_cert="foo")
        _ = index.client

        mock.assert_called_once_with(verify="foo", cert=None, trust_env=True)

    def test_client_cert(self, mocker):
        mock = mocker.patch("httpx._transports.default.create_ssl_context")
        index = PackageIndex("https://foo.internal/a/b/", client_cert="foo")
        _ = index.client

        mock.assert_called_once_with(verify=True, cert="foo", trust_env=True)

    def test_client_cert_with_key(self, mocker):
        mock = mocker.patch("httpx._transports.default.create_ssl_context")
        index = PackageIndex("https://foo.internal/a/b/", client_cert="foo", client_key="bar")
        _ = index.client

        mock.assert_called_once_with(verify=True, cert=("foo", "bar"), trust_env=True)


class TestUserAgent:
    def test_user_agent_header_format(self):
        index = PackageIndex("https://foo.internal/a/b/")
        client = index.client

        user_agent = client.headers["User-Agent"]

        assert user_agent.startswith(f"Hatch/{__version__} ")
        assert user_agent.endswith(f" HTTPX/{httpx.__version__}")

    def _extract_json_from_user_agent(self, user_agent: str) -> dict:
        json_start = user_agent.index("{")
        json_end = user_agent.rindex("}") + 1
        return json.loads(user_agent[json_start:json_end])

    def test_user_agent_contains_linehaul_json(self):
        index = PackageIndex("https://foo.internal/a/b/")
        client = index.client

        user_agent = client.headers["User-Agent"]
        data = self._extract_json_from_user_agent(user_agent)

        assert data["installer"]["name"] == "hatch"
        assert data["installer"]["version"] == __version__
        assert data["python"] == platform.python_version()
        assert data["implementation"]["name"] == platform.python_implementation()
        assert data["system"]["name"] == platform.system()
        assert data["cpu"] == platform.machine()

    def test_user_agent_linehaul_ci_detection(self, monkeypatch):
        get_linehaul_component.cache_clear()
        monkeypatch.setenv("CI", "true")

        index = PackageIndex("https://foo.internal/a/b/")
        client = index.client

        user_agent = client.headers["User-Agent"]
        data = self._extract_json_from_user_agent(user_agent)

        assert data["ci"] is True

    def test_user_agent_linehaul_macos_distro(self, mocker):
        get_linehaul_component.cache_clear()
        mocker.patch("hatch.utils.linehaul.sys.platform", "darwin")
        mocker.patch("hatch.utils.linehaul.platform.mac_ver", return_value=("14.0", "", "arm64"))

        index = PackageIndex("https://foo.internal/a/b/")
        client = index.client

        user_agent = client.headers["User-Agent"]
        data = self._extract_json_from_user_agent(user_agent)

        assert data["distro"]["name"] == "macOS"
        assert data["distro"]["version"] == "14.0"
