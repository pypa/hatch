import platform
import sys

import httpcore
import httpx
import pytest

from hatch._version import __version__
from hatch.index.core import PackageIndex


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

        expected = (
            f"Hatch/{__version__} {sys.implementation.name}/{platform.python_version()} HTTPX/{httpx.__version__}"
        )
        assert user_agent == expected


class TestEnvProxy:
    @pytest.mark.parametrize(
        ("environment", "proxies"),
        [
            ({}, {}),
            ({"HTTP_PROXY": "http://127.0.0.1"}, {"http://": "http://127.0.0.1"}),
            (
                {"https_proxy": "http://127.0.0.1", "HTTP_PROXY": "https://127.0.0.1"},
                {"https://": "http://127.0.0.1", "http://": "https://127.0.0.1"},
            ),
            ({"all_proxy": "http://127.0.0.1"}, {"all://": "http://127.0.0.1"}),
            ({"no_proxy": "127.0.0.1"}, {"all://127.0.0.1": None}),
        ],
    )
    def test_environment_proxies(self, mocker, environment, proxies):
        mocker.patch.dict("os.environ", environment, clear=True)

        client = PackageIndex("https://foo.internal/a/b/").client
        mounts = {pattern.pattern: transport for pattern, transport in client._mounts.items()}  # noqa: SLF001

        assert mounts.keys() == proxies.keys()

        for pattern, proxy in proxies.items():
            transport = mounts[pattern]
            if proxy is None:
                assert transport is None
            else:
                assert isinstance(transport, httpx.HTTPTransport)
                assert isinstance(transport._pool, httpcore.HTTPProxy)  # noqa: SLF001
                assert transport._pool._proxy_url == httpcore.URL(proxy)  # noqa: SLF001
