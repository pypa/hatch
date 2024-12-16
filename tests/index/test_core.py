from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from hatch.index.core import PackageIndex


class TestRepo:
    def test_normalization(self):
        index = PackageIndex('Https://Foo.Internal/z/../a/b/')

        assert index.repo == 'https://foo.internal/a/b/'


class TestURLs:
    @pytest.mark.parametrize(
        ('repo_url', 'expected_url'),
        [
            pytest.param('https://upload.pypi.org/legacy/', 'https://pypi.org/simple/', id='PyPI main'),
            pytest.param('https://test.pypi.org/legacy/', 'https://test.pypi.org/simple/', id='PyPI test'),
            pytest.param('https://foo.internal/a/b/', 'https://foo.internal/a/b/%2Bsimple/', id='default'),
        ],
    )
    def test_simple(self, repo_url, expected_url):
        index = PackageIndex(repo_url)

        assert str(index.urls.simple) == expected_url

    @pytest.mark.parametrize(
        ('repo_url', 'expected_url'),
        [
            pytest.param('https://upload.pypi.org/legacy/', 'https://pypi.org/project/', id='PyPI main'),
            pytest.param('https://test.pypi.org/legacy/', 'https://test.pypi.org/project/', id='PyPI test'),
            pytest.param('https://foo.internal/a/b/', 'https://foo.internal/a/b/', id='default'),
        ],
    )
    def test_project(self, repo_url, expected_url):
        index = PackageIndex(repo_url)

        assert str(index.urls.project) == expected_url


class TestTLS:
    def test_default(self, mocker):
        mock = mocker.patch('httpx._transports.default.create_ssl_context')
        index = PackageIndex('https://foo.internal/a/b/')
        _ = index.client

        mock.assert_called_once_with(verify=True, cert=None, trust_env=True)

    def test_ca_cert(self, mocker):
        mock = mocker.patch('httpx._transports.default.create_ssl_context')
        index = PackageIndex('https://foo.internal/a/b/', ca_cert='foo')
        _ = index.client

        mock.assert_called_once_with(verify='foo', cert=None, trust_env=True)

    def test_client_cert(self, mocker):
        mock = mocker.patch('httpx._transports.default.create_ssl_context')
        index = PackageIndex('https://foo.internal/a/b/', client_cert='foo')
        _ = index.client

        mock.assert_called_once_with(verify=True, cert='foo', trust_env=True)

    def test_client_cert_with_key(self, mocker):
        mock = mocker.patch('httpx._transports.default.create_ssl_context')
        index = PackageIndex('https://foo.internal/a/b/', client_cert='foo', client_key='bar')
        _ = index.client

        mock.assert_called_once_with(verify=True, cert=('foo', 'bar'), trust_env=True)


def test_upload_artifact_http_error():
    package_index = PackageIndex(repo='')
    mock_response = MagicMock()
    mock_response.is_error = True
    mock_response.status_code = 400
    mock_response.reason_phrase = 'Bad Request'
    # test real response content from pypi
    mock_response.text = """
<html>
 <head>
  <title>400 This filename has already been used, use a different version. See https://test.pypi.org/help/#file-name-reuse for more information.</title>
 </head>
 <body>
  <h1>400 This filename has already been used, use a different version. See https://test.pypi.org/help/#file-name-reuse for more information.</h1>
  The server could not comply with the request since it is either malformed or otherwise incorrect.<br/><br/>
This filename has already been used, use a different version. See https://test.pypi.org/help/#file-name-reuse for more information.
 </body>
</html>
"""
    package_index.client.post = MagicMock(return_value=mock_response)
    artifact = Path('dummy_artifact.txt')
    artifact.write_text('dummy content')
    data = {}
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        package_index.upload_artifact(artifact, data)
    artifact.unlink()
    assert (
        '400 This filename has already been used, use a different version. See https://test.pypi.org/help/#file-name-reuse for more information.'
        in str(exc_info.value)
    )
