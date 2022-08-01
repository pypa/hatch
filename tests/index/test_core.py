import pytest

from hatch.index.core import PackageIndex


class TestRepo:
    def test_normalization(self):
        index = PackageIndex('Https://Foo.Internal/z/../a/b/')

        assert index.repo == 'https://foo.internal/a/b/'


class TestURLs:
    @pytest.mark.parametrize(
        'repo_url, expected_url',
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
        'repo_url, expected_url',
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
        mock = mocker.patch('httpx.create_ssl_context')
        _ = PackageIndex('https://foo.internal/a/b/')

        mock.assert_called_once_with(verify=True, cert=None)

    def test_ca_cert(self, mocker):
        mock = mocker.patch('httpx.create_ssl_context')
        _ = PackageIndex('https://foo.internal/a/b/', ca_cert='foo')

        mock.assert_called_once_with(verify='foo', cert=None)

    def test_client_cert(self, mocker):
        mock = mocker.patch('httpx.create_ssl_context')
        _ = PackageIndex('https://foo.internal/a/b/', client_cert='foo')

        mock.assert_called_once_with(verify=True, cert='foo')

    def test_client_cert_with_key(self, mocker):
        mock = mocker.patch('httpx.create_ssl_context')
        _ = PackageIndex('https://foo.internal/a/b/', client_cert='foo', client_key='bar')

        mock.assert_called_once_with(verify=True, cert=('foo', 'bar'))
