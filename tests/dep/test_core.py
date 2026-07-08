from hatch.dep.core import Dependency
from hatch.utils.fs import Path


class TestPath:
    def test_no_url(self):
        assert Dependency("foo").path is None

    def test_non_file_scheme(self):
        assert Dependency("foo @ https://example.com/foo.tgz").path is None

    def test_file_url(self):
        dep = Dependency("foo @ file:///monorepo/pkg")

        assert dep.path == Path.from_uri("file:///monorepo/pkg")

    def test_fragment_stripped(self):
        dep = Dependency("foo @ file:///monorepo#subdirectory=packages/foo")

        assert dep.path == Path.from_uri("file:///monorepo")


class TestSubdirectory:
    def test_no_url(self):
        assert Dependency("foo").subdirectory is None

    def test_no_fragment(self):
        assert Dependency("foo @ file:///monorepo/pkg").subdirectory is None

    def test_file_url_fragment(self):
        dep = Dependency("foo @ file:///monorepo#subdirectory=packages/foo")

        assert dep.subdirectory == "packages/foo"

    def test_fragment_with_other_parameters(self):
        dep = Dependency("foo @ file:///foo.tar.gz#sha256=abc&subdirectory=pkg")

        assert dep.subdirectory == "pkg"

    def test_git_url_fragment(self):
        dep = Dependency("foo @ git+https://example.com/foo@abc#subdirectory=pkg")

        assert dep.subdirectory == "pkg"
