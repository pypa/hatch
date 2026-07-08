import pytest

from hatch.project.sources import (
    GitSource,
    IndexSource,
    PathSource,
    UrlSource,
    WorkspaceSource,
    apply_source_to_requirement,
    collect_global_install_args,
    decorate_dependencies,
    decorate_dependency,
    describe_source,
    parse_source,
    parse_sources,
    render_git_url,
    render_path_url,
    render_url,
)


class TestParseSource:
    def test_string_shorthand(self):
        source = parse_source("foo", "./packages/foo")

        assert isinstance(source, PathSource)
        assert source.path == "./packages/foo"
        assert source.editable is True
        assert source.subdirectory is None

    def test_empty_string(self):
        with pytest.raises(ValueError, match="Field `tool.hatch.sources.foo` cannot be an empty string"):
            parse_source("foo", "")

    def test_not_string_or_table(self):
        with pytest.raises(TypeError, match="Field `tool.hatch.sources.foo` must be a string or a table"):
            parse_source("foo", 9000)

    def test_no_type_key(self):
        with pytest.raises(ValueError, match="Field `tool.hatch.sources.foo` must define exactly one of:"):
            parse_source("foo", {"editable": True})

    def test_multiple_type_keys(self):
        with pytest.raises(ValueError, match="Field `tool.hatch.sources.foo` must define only one of:"):
            parse_source("foo", {"path": "./foo", "git": "https://example.com/foo"})

    def test_path_full(self):
        source = parse_source("foo", {"path": "./packages/foo", "editable": False, "subdirectory": "src"})

        assert isinstance(source, PathSource)
        assert source.path == "./packages/foo"
        assert source.editable is False
        assert source.subdirectory == "src"

    def test_path_default_editable(self):
        source = parse_source("foo", {"path": "./foo"})

        assert source.editable is True

    def test_path_not_string(self):
        with pytest.raises(TypeError, match="Field `tool.hatch.sources.foo.path` must be a string"):
            parse_source("foo", {"path": 9000})

    def test_path_empty(self):
        with pytest.raises(ValueError, match="Field `tool.hatch.sources.foo.path` cannot be an empty string"):
            parse_source("foo", {"path": ""})

    def test_path_editable_not_bool(self):
        with pytest.raises(TypeError, match="Field `tool.hatch.sources.foo.editable` must be a boolean"):
            parse_source("foo", {"path": "./foo", "editable": "yes"})

    def test_git_minimal(self):
        source = parse_source("foo", {"git": "https://example.com/foo"})

        assert isinstance(source, GitSource)
        assert source.git == "https://example.com/foo"
        assert source.reference is None

    def test_git_with_rev(self):
        source = parse_source("foo", {"git": "https://example.com/foo", "rev": "abc123"})

        assert source.rev == "abc123"
        assert source.reference == "abc123"

    def test_git_with_tag(self):
        source = parse_source("foo", {"git": "https://example.com/foo", "tag": "v1.0"})

        assert source.tag == "v1.0"
        assert source.reference == "v1.0"

    def test_git_with_branch(self):
        source = parse_source("foo", {"git": "https://example.com/foo", "branch": "main"})

        assert source.branch == "main"
        assert source.reference == "main"

    def test_git_multiple_refs(self):
        with pytest.raises(ValueError, match="Field `tool.hatch.sources.foo` must define only one of:"):
            parse_source("foo", {"git": "https://example.com/foo", "rev": "abc", "tag": "v1.0"})

    def test_git_empty(self):
        with pytest.raises(ValueError, match="Field `tool.hatch.sources.foo.git` cannot be an empty string"):
            parse_source("foo", {"git": ""})

    def test_url(self):
        source = parse_source("foo", {"url": "https://example.com/foo.tar.gz", "subdirectory": "pkg"})

        assert isinstance(source, UrlSource)
        assert source.url == "https://example.com/foo.tar.gz"
        assert source.subdirectory == "pkg"

    def test_url_empty(self):
        with pytest.raises(ValueError, match="Field `tool.hatch.sources.foo.url` cannot be an empty string"):
            parse_source("foo", {"url": ""})

    def test_index(self):
        source = parse_source("foo", {"index": "https://pypi.example.com/simple"})

        assert isinstance(source, IndexSource)
        assert source.index == "https://pypi.example.com/simple"

    def test_index_empty(self):
        with pytest.raises(ValueError, match="Field `tool.hatch.sources.foo.index` cannot be an empty string"):
            parse_source("foo", {"index": ""})

    def test_workspace(self):
        source = parse_source("foo", {"workspace": True})

        assert isinstance(source, WorkspaceSource)

    def test_workspace_false(self):
        with pytest.raises(ValueError, match="Field `tool.hatch.sources.foo.workspace` must be `true`"):
            parse_source("foo", {"workspace": False})

    def test_workspace_not_bool(self):
        with pytest.raises(TypeError, match="Field `tool.hatch.sources.foo.workspace` must be a boolean"):
            parse_source("foo", {"workspace": "yes"})


class TestParseSources:
    def test_default(self):
        assert parse_sources({}) == {}

    def test_not_table(self):
        with pytest.raises(TypeError, match="Field `tool.hatch.sources` must be a table"):
            parse_sources(9000)

    def test_basic(self):
        sources = parse_sources({
            "foo": "./packages/foo",
            "bar": {"git": "https://example.com/bar"},
        })

        assert set(sources) == {"foo", "bar"}
        assert isinstance(sources["foo"], PathSource)
        assert isinstance(sources["bar"], GitSource)

    def test_normalized_keys(self):
        sources = parse_sources({"My_Pkg.Name": "./pkg"})

        assert "my-pkg-name" in sources

    def test_duplicate_after_normalization(self):
        with pytest.raises(ValueError, match="Field `tool.hatch.sources` contains duplicate names:"):
            parse_sources({"my-pkg": "./pkg", "my_pkg": "./pkg2"})

    def test_empty_name(self):
        with pytest.raises(ValueError, match="Source names in `tool.hatch.sources` cannot be empty"):
            parse_sources({"": "./pkg"})

    def test_custom_root_field_in_errors(self):
        root_field = "tool.hatch.envs.test.sources"

        with pytest.raises(TypeError, match="Field `tool.hatch.envs.test.sources` must be a table"):
            parse_sources(9000, root_field=root_field)

        with pytest.raises(TypeError, match="Field `tool.hatch.envs.test.sources.foo.path` must be a string"):
            parse_sources({"foo": {"path": 9000}}, root_field=root_field)

        with pytest.raises(ValueError, match="Field `tool.hatch.envs.test.sources` contains duplicate names:"):
            parse_sources({"my-pkg": "./pkg", "my_pkg": "./pkg2"}, root_field=root_field)


class TestRender:
    def test_render_path_url_relative(self, temp_dir):
        url = render_path_url("subdir/pkg", str(temp_dir))

        assert url.startswith("file://")
        assert url.endswith("subdir/pkg")

    def test_render_path_url_absolute(self, temp_dir):
        absolute = str(temp_dir / "pkg")

        url = render_path_url(absolute, str(temp_dir))

        assert url == temp_dir.joinpath("pkg").resolve().as_uri()

    def test_render_path_url_subdirectory(self, temp_dir):
        url = render_path_url("pkg", str(temp_dir), subdirectory="src")

        assert url.endswith("#subdirectory=src")

    def test_render_git_url_no_ref(self):
        source = GitSource(git="https://example.com/foo")

        assert render_git_url(source) == "git+https://example.com/foo"

    def test_render_git_url_with_ref(self):
        source = GitSource(git="https://example.com/foo", rev="abc123")

        assert render_git_url(source) == "git+https://example.com/foo@abc123"

    def test_render_git_url_with_subdirectory(self):
        source = GitSource(git="https://example.com/foo", tag="v1", subdirectory="pkg")

        assert render_git_url(source) == "git+https://example.com/foo@v1#subdirectory=pkg"

    def test_render_url_simple(self):
        source = UrlSource(url="https://example.com/foo.tgz")

        assert render_url(source) == "https://example.com/foo.tgz"

    def test_render_url_with_subdirectory(self):
        source = UrlSource(url="https://example.com/foo.tgz", subdirectory="pkg")

        assert render_url(source) == "https://example.com/foo.tgz#subdirectory=pkg"

    def test_render_url_with_existing_fragment(self):
        source = UrlSource(url="https://example.com/foo.tgz#sha256=abc", subdirectory="pkg")

        assert render_url(source) == "https://example.com/foo.tgz#sha256=abc&subdirectory=pkg"


class TestApplySourceToRequirement:
    def test_path_editable(self, temp_dir):
        source = PathSource(path="pkg", editable=True)

        result = apply_source_to_requirement("foo", [], source, str(temp_dir))

        assert result is not None
        spec, editable = result
        assert spec.startswith("foo @ file://")
        assert editable is True

    def test_path_with_extras(self, temp_dir):
        source = PathSource(path="pkg")

        result = apply_source_to_requirement("foo", ["a", "b"], source, str(temp_dir))

        assert result is not None
        spec, _ = result
        assert spec.startswith("foo[a,b] @ file://")

    def test_path_editable_with_subdirectory_joins_path(self, temp_dir):
        source = PathSource(path="monorepo", editable=True, subdirectory="packages/foo")

        result = apply_source_to_requirement("foo", [], source, str(temp_dir))

        assert result is not None
        spec, editable = result
        assert editable is True
        # Editable installs pass a bare directory to the installer, so the
        # subdirectory must be part of the path rather than a URL fragment
        assert "#subdirectory" not in spec
        assert spec.endswith("monorepo/packages/foo")

    def test_path_non_editable_with_subdirectory_uses_fragment(self, temp_dir):
        source = PathSource(path="monorepo", editable=False, subdirectory="packages/foo")

        result = apply_source_to_requirement("foo", [], source, str(temp_dir))

        assert result is not None
        spec, editable = result
        assert editable is False
        assert spec.endswith("#subdirectory=packages/foo")

    def test_git(self, temp_dir):
        source = GitSource(git="https://example.com/foo", rev="abc")

        result = apply_source_to_requirement("foo", [], source, str(temp_dir))

        assert result == ("foo @ git+https://example.com/foo@abc", False)

    def test_url(self, temp_dir):
        source = UrlSource(url="https://example.com/foo.tgz")

        result = apply_source_to_requirement("foo", [], source, str(temp_dir))

        assert result == ("foo @ https://example.com/foo.tgz", False)

    def test_index_returns_none(self, temp_dir):
        source = IndexSource(index="https://pypi.example.com/simple")

        assert apply_source_to_requirement("foo", [], source, str(temp_dir)) is None

    def test_workspace_returns_none(self, temp_dir):
        source = WorkspaceSource()

        assert apply_source_to_requirement("foo", [], source, str(temp_dir)) is None

    def test_workspace_resolves_to_member(self, temp_dir):
        source = WorkspaceSource()
        member_path = str(temp_dir / "members" / "foo")
        workspace_members = {"foo": member_path}

        result = apply_source_to_requirement("foo", [], source, str(temp_dir), workspace_members)

        assert result is not None
        spec, editable = result
        assert spec.startswith("foo @ file://")
        assert spec.endswith("members/foo")
        assert editable is True

    def test_workspace_unmatched_member_returns_none(self, temp_dir):
        source = WorkspaceSource()

        # `bar` is not present in the member mapping
        assert apply_source_to_requirement("foo", [], source, str(temp_dir), {"bar": str(temp_dir)}) is None


class TestDecorateDependency:
    def test_no_sources(self, temp_dir):
        from hatch.dep.core import Dependency

        dep = Dependency("foo>=1")

        result = decorate_dependency(dep, {}, str(temp_dir))

        assert result is dep

    def test_path_source_rewrites(self, temp_dir):
        from hatch.dep.core import Dependency

        dep = Dependency("foo>=1")
        sources = {"foo": PathSource(path="pkg")}

        result = decorate_dependency(dep, sources, str(temp_dir))

        assert result is not dep
        assert result.url is not None
        assert result.url.startswith("file://")
        assert result.editable is True
        assert isinstance(result.source, PathSource)

    def test_index_source_attached_without_rewrite(self, temp_dir):
        from hatch.dep.core import Dependency

        dep = Dependency("foo>=1")
        sources = {"foo": IndexSource(index="https://pypi.example.com/simple")}

        result = decorate_dependency(dep, sources, str(temp_dir))

        assert result.url is None
        assert isinstance(result.source, IndexSource)

    def test_existing_url_preserved(self, temp_dir):
        from hatch.dep.core import Dependency

        dep = Dependency("foo @ https://override.example.com/foo.tgz")
        sources = {"foo": PathSource(path="pkg")}

        result = decorate_dependency(dep, sources, str(temp_dir))

        # PEP 508 direct references win — the user explicitly chose the URL
        assert result is dep

    def test_marker_preserved(self, temp_dir):
        from hatch.dep.core import Dependency

        dep = Dependency('foo>=1; sys_platform == "linux"')
        sources = {"foo": PathSource(path="pkg")}

        result = decorate_dependency(dep, sources, str(temp_dir))

        assert result.marker is not None
        assert "linux" in str(result.marker)

    def test_normalized_lookup(self, temp_dir):
        from hatch.dep.core import Dependency

        dep = Dependency("My_Pkg.Name>=1")
        sources = {"my-pkg-name": PathSource(path="pkg")}

        result = decorate_dependency(dep, sources, str(temp_dir))

        assert result.url is not None

    def test_workspace_source_resolves_to_member(self, temp_dir):
        from hatch.dep.core import Dependency

        dep = Dependency("foo>=1")
        sources = {"foo": WorkspaceSource()}
        member_path = str(temp_dir / "members" / "foo")

        result = decorate_dependency(dep, sources, str(temp_dir), {"foo": member_path})

        assert result is not dep
        assert result.url is not None
        assert result.url.startswith("file://")
        assert result.editable is True
        assert isinstance(result.source, WorkspaceSource)

    def test_workspace_source_unmatched_raises(self, temp_dir):
        from hatch.dep.core import Dependency

        dep = Dependency("foo>=1")
        sources = {"foo": WorkspaceSource()}

        with pytest.raises(
            ValueError,
            match="Dependency `foo` declares `workspace = true` in `tool.hatch.sources` but no matching member",
        ):
            decorate_dependency(dep, sources, str(temp_dir), {})


class TestDecorateDependencies:
    def test_empty_sources(self, temp_dir):
        from hatch.dep.core import Dependency

        deps = [Dependency("foo"), Dependency("bar")]

        result = decorate_dependencies(deps, {}, str(temp_dir))

        assert result == deps


class TestCollectGlobalInstallArgs:
    def test_empty(self):
        assert collect_global_install_args([]) == []

    def test_index_sources(self):
        sources = [
            IndexSource(index="https://example.com/a"),
            IndexSource(index="https://example.com/b"),
        ]

        assert collect_global_install_args(sources) == [
            "--extra-index-url",
            "https://example.com/a",
            "--extra-index-url",
            "https://example.com/b",
        ]

    def test_dedupe(self):
        sources = [
            IndexSource(index="https://example.com/a"),
            IndexSource(index="https://example.com/a"),
        ]

        assert collect_global_install_args(sources) == [
            "--extra-index-url",
            "https://example.com/a",
        ]

    def test_non_index_sources_ignored(self):
        sources = [PathSource(path="pkg"), GitSource(git="https://example.com/foo")]

        assert collect_global_install_args(sources) == []


class TestDescribeSource:
    def test_path(self):
        assert describe_source(PathSource(path="./pkg")) == ("path", "./pkg")

    def test_path_with_options(self):
        source = PathSource(path="./monorepo", editable=False, subdirectory="pkg")

        assert describe_source(source) == ("path", "./monorepo (subdirectory: pkg) (not editable)")

    def test_git(self):
        source = GitSource(git="https://example.com/foo", tag="v1")

        assert describe_source(source) == ("git", "git+https://example.com/foo@v1")

    def test_url(self):
        source = UrlSource(url="https://example.com/foo.tgz")

        assert describe_source(source) == ("url", "https://example.com/foo.tgz")

    def test_index(self):
        source = IndexSource(index="https://pypi.example.com/simple")

        assert describe_source(source) == ("index", "https://pypi.example.com/simple")

    def test_workspace(self):
        assert describe_source(WorkspaceSource()) == ("workspace", "resolved via `workspace.members`")
