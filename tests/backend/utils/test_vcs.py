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
        ("/pkg/", True),
        ("p?g/", True),
        ("p[k]g", True),
        ("pkg/**", False),
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


def test_nearest_ignore_file_selects_contents(temp_dir):
    root = temp_dir / "pkg"
    root.mkdir()
    (temp_dir / ".gitignore").write_text("*.py\n")
    (root / ".gitignore").write_text("*.txt\n")

    policy = VCSIgnorePolicy(str(root))
    spec = ExclusionSpec([], policy.sources, [])

    assert spec.match_file("file.txt")
    assert not spec.match_file("file.py")


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
