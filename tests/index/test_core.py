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
