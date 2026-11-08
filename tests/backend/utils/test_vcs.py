import os
import subprocess

import pytest

from hatchling.utils.vcs import ExclusionSpec, IgnoreSource, VCSIgnorePolicy


@pytest.mark.parametrize("vcs", ["git", "hg"])
@pytest.mark.parametrize(
    ("patterns", "ignored"),
    [
        ("*", True),
        ("pkg/", True),
        ("pkg/ \n", True),
        ("/pkg/", True),
        ("p?g/", True),
        ("p[k]g", True),
        ("pkg/**", False),
        ("pkg/**/", False),
        ("pkg/*", False),
        ("*\n!/pkg/", False),
        ("/pkg/\n!/pkg/", False),
        ("pkg/\n!pkg/file.py", True),
        ("*.py", False),
    ],
)
def test_ignored_project(temp_dir, vcs, patterns, ignored):
    root = temp_dir / "pkg"
    root.mkdir()
    header = "syntax: glob\n" if vcs == "hg" else ""
    (temp_dir / f".{vcs}ignore").write_text(header + patterns)
    (root / f".{vcs}ignore").write_text(header + "local.txt\n")

    policy = VCSIgnorePolicy(str(root))

    assert policy.parent_ignored is ignored
    assert ExclusionSpec([], policy.sources, []).match_file("local.txt")
    if ignored:
        assert all(not source.prefix for source in policy.sources)


@pytest.mark.parametrize("directory", ["dist", "build", "var"])
def test_local_rules_cannot_exclude_containing_project(temp_dir, directory):
    root = temp_dir / directory / "pkg"
    root.mkdir(parents=True)
    (root / ".gitignore").write_text(f"{directory}/\nprivate.txt\n")

    policy = VCSIgnorePolicy(str(root))
    spec = ExclusionSpec([], policy.sources, [])

    assert not policy.parent_ignored
    assert spec.match_file("private.txt")
    assert not spec.match_file("module.py")


@pytest.mark.parametrize(
    ("outer", "inner", "ignored"),
    [
        ("build/", "!pkg/", True),
        ("build/*", "!pkg/", False),
        ("*\n!build/", "!pkg/", False),
        ("build/pkg/", "*.py", True),
    ],
)
def test_ancestor_precedence(temp_dir, outer, inner, ignored):
    root = temp_dir / "build" / "pkg"
    root.mkdir(parents=True)
    (temp_dir / ".gitignore").write_text(outer)
    (root.parent / ".gitignore").write_text(inner)

    assert VCSIgnorePolicy(str(root)).parent_ignored is ignored


@pytest.mark.parametrize("vcs", ["git", "hg"])
@pytest.mark.parametrize("boundary", ["directory", "file"])
def test_repository_boundary(temp_dir, vcs, boundary):
    root = temp_dir / "repo" / "pkg"
    root.mkdir(parents=True)
    (temp_dir / f".{vcs}ignore").write_text("*\n" if vcs == "git" else "syntax: glob\n*\n")
    marker = root.parent / f".{vcs}"
    if boundary == "directory":
        marker.mkdir()
    else:
        marker.write_text("gitdir: ../other/worktrees/repo\n")

    policy = VCSIgnorePolicy(str(root))

    assert not policy.parent_ignored
    assert not policy.sources


@pytest.mark.parametrize("ignored_vcs", ["git", "hg"])
def test_ignored_project_rejects_all_inherited_sources(temp_dir, ignored_vcs):
    root = temp_dir / "pkg"
    root.mkdir()
    (temp_dir / ".gitignore").write_text("*" if ignored_vcs == "git" else "*.py")
    (temp_dir / ".hgignore").write_text("syntax: glob\n" + ("*" if ignored_vcs == "hg" else "*.py"))

    policy = VCSIgnorePolicy(str(root))

    assert policy.parent_ignored
    assert not policy.sources


def test_sdist_boundary(temp_dir):
    root = temp_dir / "pkg"
    root.mkdir()
    (root / "PKG-INFO").touch()
    (temp_dir / ".gitignore").write_text("*.py\n")
    (temp_dir / ".hgignore").write_text("syntax: glob\n*.txt\n")

    policy = VCSIgnorePolicy(str(root))

    assert policy.isolated
    assert not policy.sources


def test_local_ignore_file_inherits_parent_rules(temp_dir):
    root = temp_dir / "pkg"
    root.mkdir()
    (temp_dir / ".gitignore").write_text("*.py\n")
    (root / ".gitignore").write_text("*.txt\n")

    policy = VCSIgnorePolicy(str(root))
    spec = ExclusionSpec([], policy.sources, [], vcs_ignore=policy)

    assert spec.match_file("file.txt")
    assert spec.match_file("file.py")


@pytest.mark.parametrize("directory", ["", "nested/"])
def test_ignore_file_encoding(temp_dir, directory):
    root = temp_dir / "pkg"
    ignore_file = root / directory / ".gitignore"
    ignore_file.parent.mkdir(parents=True)
    ignore_file.write_bytes(b"\xef\xbb\xbfprivate.txt\r\ncache/\r\n")
    policy = VCSIgnorePolicy(str(root))
    spec = ExclusionSpec([], policy.sources, [], vcs_ignore=policy)

    assert spec.match_file(f"{directory}private.txt")
    assert spec.match_file(f"{directory}cache/file.txt")
    assert not spec.match_file(f"{directory}module.py")


@pytest.mark.requires_git
@pytest.mark.parametrize(
    ("prefix", "patterns"),
    [
        ("pkg", "pkg/private.txt\n/private.txt\n*.pyc\n"),
        ("pkg", "pkg/**\n!pkg/keep.txt\n"),
        ("pkg", "*\n!/pkg/\n!/pkg/keep.txt\n"),
        ("pkg", "pkg/\n!pkg/\n"),
        ("pkg", "**/\n!/pkg/\n"),
        ("pkg", "**/\n!pkg/\n!pkg/cache/\n"),
        ("pkg", "p?g/private.txt\n"),
        ("pkg", "p[k]g/private.txt\n"),
        ("pkg", "**/private.txt\n!pkg/keep.txt\n"),
        ("top/pkg", "top/**/private.txt\n"),
        ("top/pkg", "**/pkg/**/private.txt\n"),
        ("pkg/pkg", "**/pkg/**/private.txt\n"),
        ("top/pkg", "top/**/pkg/*\n!top/pkg/keep.txt\n"),
        ("pkg", "pkg/cache/\n!pkg/cache/keep.txt\n"),
        ("pkg", "pkg/cache/*\n!pkg/cache/keep.txt\n"),
        ("pkg", "pkg/\\#hash\npkg/\\!bang\npkg/space\\ name\n"),
        ("pkg", "# comment\n\n/private.txt\nprivate.txt\n!keep.txt"),
        ("pkg space", "pkg space/private.txt\n"),
        ("pkg[1]", "pkg\\[1\\]/private.txt\n"),
    ],
)
def test_inherited_rules_match_git(temp_dir, prefix, patterns):
    # Check the matcher used by the builders against Git.
    git = ["git", "-c", f"core.excludesFile={os.devnull}", "-c", "core.ignoreCase=false"]
    subprocess.run([*git, "init", "-q", "--template=", str(temp_dir)], check=True)
    root = temp_dir / prefix
    root.mkdir(parents=True)
    (temp_dir / ".gitignore").write_text(patterns)
    source = VCSIgnorePolicy(str(root)).sources[0]
    spec = ExclusionSpec([], [source], [])

    for name in [
        "private.txt",
        "keep.txt",
        "file.pyc",
        "module.py",
        "nested/private.txt",
        "cache/private.txt",
        "cache/keep.txt",
        "pkg/private.txt",
        "#hash",
        "!bang",
        "space name",
    ]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        result = subprocess.run([*git, "check-ignore", "-q", "--no-index", name], cwd=root, check=False)
        assert result.returncode in {0, 1}
        ignored = result.returncode == 0
        assert spec.match_file(name) is ignored, name


def test_vcs_negation_overrides_defaults():
    source = IgnoreSource("git", "pkg/", ["!pkg/dist/\n"])
    spec = ExclusionSpec(["dist/"], [source], [])

    assert not spec.match_file("dist/file.txt")
    assert spec.match_file("nested/dist/file.txt")


@pytest.mark.parametrize("prefix", ["", "pkg/"])
@pytest.mark.parametrize(("directory_rule", "ignored"), [("", False), ("dist/", True), ("dist/*", False)])
def test_vcs_file_negation_overrides_defaults(prefix, directory_rule, ignored):
    patterns = [f"{prefix}{directory_rule}"] if directory_rule else []
    patterns.append(f"!{prefix}dist/keep.txt")
    spec = ExclusionSpec(["/dist"], [IgnoreSource("git", prefix, patterns)], [])

    # Checking a default-excluded directory must not make it a VCS barrier.
    assert spec.match_file("dist/")
    assert spec.match_file("dist/keep.txt") is ignored
    assert spec.match_file("dist/drop.txt")


def test_explicit_negation_overrides_ignored_directory():
    source = IgnoreSource("git", "", ["data/\n"])
    spec = ExclusionSpec([], [source], ["!data/keep.txt"])

    assert not spec.match_file("data/keep.txt")
    assert spec.match_file("data/other.txt")


@pytest.mark.requires_git
@pytest.mark.parametrize(
    "ignore_files",
    [
        {".gitignore": "*.txt\n", "pkg/.gitignore": "*.py\n"},
        {".gitignore": "*.txt\n", "pkg/.gitignore": "!keep.txt\n"},
        {".gitignore": "*.txt\n", "pkg/demo/.gitignore": "!keep.txt\n"},
        {"pkg/demo/.gitignore": "private.txt\n"},
        {".gitignore": "pkg/demo/\n", "pkg/demo/.gitignore": "!keep.txt\n"},
        {".gitignore": "pkg/demo/*\n", "pkg/demo/.gitignore": "!keep.txt\n"},
        {".gitignore": "*.txt\n", "pkg/demo/.gitignore": "/private.txt\n!keep.txt\n"},
        {".gitignore": "pkg/*\n!pkg/demo/\n", "pkg/demo/.gitignore": "!keep.txt\n"},
        {
            ".gitignore": "*.txt\n",
            "pkg/.gitignore": "!keep.txt\n",
            "pkg/demo/.gitignore": "/keep.txt\n",
            "pkg/demo/deep/.gitignore": "!private.txt\n",
        },
    ],
)
def test_ignore_hierarchy_matches_git(temp_dir, ignore_files):
    git = ["git", "-c", f"core.excludesFile={os.devnull}", "-c", "core.ignoreCase=false"]
    subprocess.run([*git, "init", "-q", "--template=", str(temp_dir)], check=True)
    root = temp_dir / "pkg"
    root.mkdir()
    for name, contents in ignore_files.items():
        path = temp_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
    policy = VCSIgnorePolicy(str(root))
    assert not policy.parent_ignored
    spec = ExclusionSpec([], policy.sources, [], vcs_ignore=policy)
    for directory in ["", "demo/", "demo/deep/", "other/"]:
        for name in ["private.txt", "keep.txt", "module.py"]:
            path = f"{directory}{name}"
            result = subprocess.run([*git, "check-ignore", "-q", "--no-index", path], cwd=root, check=False)
            assert result.returncode in {0, 1}
            assert spec.match_file(path) is (result.returncode == 0), path


def test_nested_rules_with_an_ignored_project(temp_dir):
    root = temp_dir / "pkg"
    nested = root / "demo"
    nested.mkdir(parents=True)
    (temp_dir / ".gitignore").write_text("*\n")
    (nested / ".gitignore").write_text("private.txt\n")
    policy = VCSIgnorePolicy(str(root))
    spec = ExclusionSpec([], policy.sources, [], vcs_ignore=policy)

    assert policy.isolated
    assert spec.match_file("demo/private.txt")
    assert not spec.match_file("demo/module.py")


def test_nested_negation_overrides_defaults(temp_dir):
    root = temp_dir / "pkg"
    nested = root / "dist"
    nested.mkdir(parents=True)
    (nested / ".gitignore").write_text("!keep.txt\n")
    policy = VCSIgnorePolicy(str(root))
    spec = ExclusionSpec(["/dist"], policy.sources, [], vcs_ignore=policy)

    assert spec.match_file("dist/")
    assert not spec.match_file("dist/keep.txt")
    assert spec.match_file("dist/drop.txt")


def test_symlinked_gitignore_is_not_followed(temp_dir):
    root = temp_dir / "pkg"
    root.mkdir()
    (temp_dir / "rules").write_text("*\n")
    try:
        (root / ".gitignore").symlink_to(temp_dir / "rules")
    except OSError:
        pytest.skip("Symlinks are unavailable")
    policy = VCSIgnorePolicy(str(root))
    spec = ExclusionSpec([], policy.sources, [], vcs_ignore=policy)

    assert not spec.match_file("module.py")
