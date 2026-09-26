import os
import tarfile
from zipfile import ZipFile

import pytest

from hatchling.builders.sdist import SdistBuilder
from hatchling.builders.wheel import WheelBuilder


def make_project(root, extra_config=""):
    root.mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["hatchling"]\nbuild-backend = "hatchling.build"\n'
        '[project]\nname = "demo"\nversion = "1.0"\n'
        '[tool.hatch.build.targets.wheel]\npackages = ["demo"]\n'
        '[tool.hatch.build.targets.sdist]\nartifacts = ["demo/private.txt"]\n' + extra_config
    )
    package = root / "demo"
    package.mkdir()
    (package / "__init__.py").write_text("VALUE = 1\n")
    (package / "private.txt").write_text("sdist-only data\n")
    (package / "keep.txt").write_text("package data\n")
    return root


def wheel_files(root, output):
    with root.as_cwd():
        artifact = next(WheelBuilder(str(root)).build(directory=str(output)))
    with ZipFile(artifact) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def extract_sdist(root, output, destination, helpers):
    with root.as_cwd():
        builder = SdistBuilder(str(root))
        artifact = next(builder.build(directory=str(output)))
    with tarfile.open(artifact) as archive:
        names = [name for name in archive.getnames() if name.endswith(("/.gitignore", "/.hgignore"))]
        assert len(names) == len(set(names))
        archive.extractall(destination, **helpers.tarfile_extraction_compat_options())
    return destination / builder.artifact_project_id


@pytest.mark.parametrize("vcs", ["git", "hg"])
@pytest.mark.parametrize(
    ("parent_patterns", "local_patterns", "private_excluded", "code_excluded"),
    [
        ("*\n", None, False, False),
        ("pkg/\n*.py\n", None, False, False),
        ("/pkg/\n", None, False, False),
        ("*\n", "demo/private.txt\ndist/\n", True, False),
        ("pkg/\n", "*\n", True, True),
        ("*.txt\n", "demo/private.txt\ndist/\n", True, False),
    ],
)
def test_sdist_round_trip(temp_dir, helpers, vcs, parent_patterns, local_patterns, private_excluded, code_excluded):
    root = make_project(temp_dir / "repository" / "pkg")
    header = "syntax: glob\n" if vcs == "hg" else ""
    (root.parent / f".{vcs}ignore").write_text(header + parent_patterns)
    if local_patterns is not None:
        (root / f".{vcs}ignore").write_text(header + local_patterns)
    original = wheel_files(root, temp_dir / "original-wheel")
    assert ("demo/private.txt" not in original) is private_excluded
    assert ("demo/__init__.py" not in original) is code_excluded

    # Relocation must not introduce rules or configuration from the extracting repo.
    destination = temp_dir / "unrelated" / "dist"
    destination.mkdir(parents=True)
    (destination / ".gitignore").write_text("*.py\n*.txt\n")
    (destination / ".hgignore").write_text("syntax: glob\n*.py\n*.txt\n")
    (destination / "hatch.toml").write_text('[build]\nexclude = ["*"]\n')
    extracted = extract_sdist(root, temp_dir / "sdist", destination, helpers)
    assert (extracted / "demo" / "private.txt").is_file()

    ignore_file = extracted / f".{vcs}ignore"
    if local_patterns is not None:
        assert ignore_file.read_text() == header + local_patterns
    else:
        assert not ignore_file.exists()
    assert wheel_files(extracted, temp_dir / "rebuilt-wheel") == original

    second = extract_sdist(extracted, temp_dir / "second-sdist", temp_dir / "build", helpers)
    assert wheel_files(second, temp_dir / "second-wheel") == original


@pytest.mark.parametrize("vcs", ["git", "hg"])
@pytest.mark.parametrize(
    "patterns", ["pkg/demo/private.txt\n/demo/keep.txt\n", "p?g/**/private.txt\n", "pkg/**\n", "*.txt\n"]
)
def test_parent_ignore_is_not_copied(temp_dir, helpers, vcs, patterns):
    root = make_project(temp_dir / "repository" / "pkg")
    contents = f"syntax: glob\n{patterns}" if vcs == "hg" else patterns
    parent_ignore = root.parent / f".{vcs}ignore"
    parent_ignore.write_text(contents)
    original = wheel_files(root, temp_dir / "original-wheel")
    assert "demo/private.txt" not in original

    destination = temp_dir / "unrelated" / "dist"
    destination.mkdir(parents=True)
    (destination / ".gitignore").write_text("*.py\n*.txt\n")
    (destination / ".hgignore").write_text("syntax: glob\n*.py\n*.txt\n")
    extracted = extract_sdist(root, temp_dir / "sdist", destination, helpers)

    assert not (extracted / ".gitignore").exists()
    assert not (extracted / ".hgignore").exists()
    assert not (root / f".{vcs}ignore").exists()
    assert parent_ignore.read_text() == contents

    # The sdist explicitly includes this artifact. Parent-only rules are no longer
    # available when rebuilding, so exclusions needed there must be project-local.
    rebuilt = wheel_files(extracted, temp_dir / "rebuilt-wheel")
    expected_package = {name: data for name, data in original.items() if name.startswith("demo/")}
    expected_package["demo/private.txt"] = (root / "demo" / "private.txt").read_bytes()
    assert {name: data for name, data in rebuilt.items() if name.startswith("demo/")} == expected_package

    second = extract_sdist(extracted, temp_dir / "second-sdist", temp_dir / "build", helpers)
    assert wheel_files(second, temp_dir / "second-wheel") == rebuilt


@pytest.mark.parametrize("directory", ["dist", "build", "var"])
def test_local_ignore_in_matching_ancestor_directory(temp_dir, helpers, directory):
    root = make_project(temp_dir / directory / "pkg")
    (root / ".gitignore").write_text(f"{directory}/\ndemo/private.txt\n")
    original = wheel_files(root, temp_dir / "wheel")
    assert "demo/private.txt" not in original
    assert "demo/__init__.py" in original

    extracted = extract_sdist(root, temp_dir / "sdist", temp_dir / directory / "extracted", helpers)
    assert (extracted / "demo" / "private.txt").exists()
    assert wheel_files(extracted, temp_dir / "rebuilt") == original


@pytest.mark.parametrize(
    "directory", ["plain", "build", "dist", "lib", "var", "env", "venv", "var/lib/jenkins/workspace"]
)
def test_local_env_exclusion_in_sdist(temp_dir, helpers, directory):
    # https://github.com/pypa/hatch/issues/1964#issuecomment-5849712352
    root = make_project(temp_dir / directory / "proj")
    patterns = "build/\ndist/\nlib/\nvar/\nenv/\nvenv/\n.env\n"
    (root / ".gitignore").write_text(patterns)
    (root / ".env").write_text("EXAMPLE_VALUE=test\n")
    (root / ".env.example").write_text("EXAMPLE_VALUE=\n")

    extracted = extract_sdist(root, temp_dir / "sdist", temp_dir / "extracted", helpers)

    assert not (extracted / ".env").exists()
    assert (extracted / ".env.example").is_file()
    assert (extracted / "demo" / "__init__.py").is_file()
    assert (extracted / ".gitignore").read_text() == patterns


def test_ignored_parent_preserves_explicit_external_inputs(temp_dir, helpers):
    root = make_project(
        temp_dir / "pkg",
        '\n[tool.hatch.build.force-include]\n"../asset.txt" = "demo/asset.txt"\n',
    )
    (temp_dir / ".gitignore").write_text("*\n")
    asset = temp_dir / "asset.txt"
    asset.write_text("external asset\n")

    assert wheel_files(root, temp_dir / "wheel")["demo/asset.txt"] == asset.read_bytes()
    extracted = extract_sdist(root, temp_dir / "sdist", temp_dir / "extracted", helpers)
    assert (extracted / "demo" / "asset.txt").read_bytes() == asset.read_bytes()
    assert not (extracted / ".gitignore").exists()


def test_explicit_excludes_and_artifacts_override_vcs(temp_dir):
    root = make_project(
        temp_dir / "pkg",
        '\n[tool.hatch.build]\nexclude = ["demo/keep.txt"]\nartifacts = ["demo/private.txt"]\n',
    )
    (root / ".gitignore").write_text("demo/*.txt\n!demo/keep.txt\n")

    files = wheel_files(root, temp_dir / "wheel")

    assert "demo/private.txt" in files
    assert "demo/keep.txt" not in files


@pytest.mark.parametrize("ignored_by_vcs", [False, True])
def test_sdist_vcs_negation_overrides_default_exclusion(temp_dir, helpers, ignored_by_vcs):
    root = make_project(temp_dir / "pkg")
    patterns = ("dist/\n" if ignored_by_vcs else "") + "!dist/keep.txt\n"
    (root / ".gitignore").write_text(patterns)
    (root / "dist").mkdir()
    (root / "dist" / "keep.txt").write_text("selected data\n")
    (root / "dist" / "drop.txt").write_text("excluded data\n")

    extracted = extract_sdist(root, temp_dir / "sdist", temp_dir / "extracted", helpers)

    assert (extracted / "dist" / "keep.txt").exists() is not ignored_by_vcs
    assert not (extracted / "dist" / "drop.txt").exists()


def test_ignore_vcs_option(temp_dir, helpers):
    root = make_project(temp_dir / "pkg", "\n[tool.hatch.build]\nignore-vcs = true\n")
    (temp_dir / ".gitignore").write_text("pkg/demo/private.txt\n")
    original = wheel_files(root, temp_dir / "wheel")
    assert "demo/private.txt" in original

    extracted = extract_sdist(root, temp_dir / "sdist", temp_dir / "extracted", helpers)
    assert not (extracted / ".gitignore").exists()
    assert wheel_files(extracted, temp_dir / "rebuilt") == original


@pytest.mark.parametrize("vcs", ["git", "hg"])
def test_parent_ignore_can_be_explicitly_included(temp_dir, helpers, vcs):
    root = make_project(
        temp_dir / "pkg",
        f'\n[tool.hatch.build.targets.sdist.force-include]\n"../.{vcs}ignore" = ".{vcs}ignore"\n',
    )
    patterns = "pkg/demo/private.txt\n"
    contents = f"syntax: glob\n{patterns}" if vcs == "hg" else patterns
    (temp_dir / f".{vcs}ignore").write_text(contents)

    extracted = extract_sdist(root, temp_dir / "sdist", temp_dir / "extracted", helpers)

    assert (extracted / f".{vcs}ignore").read_text() == contents


@pytest.mark.parametrize("ignore_root", [False, True])
@pytest.mark.parametrize("self_excluded", [False, True])
@pytest.mark.parametrize("explicit_files", [False, True])
def test_nested_ignore_round_trip(temp_dir, helpers, ignore_root, self_excluded, explicit_files):
    extra_config = (
        'only-include = ["demo/private.txt", "demo/__init__.py", "demo/keep.txt"]\n' if explicit_files else ""
    )
    root = make_project(temp_dir / "repository" / "pkg", extra_config)
    if ignore_root:
        (root.parent / ".gitignore").write_text("pkg/\n")
    patterns = "private.txt\n" + (".gitignore\n" if self_excluded else "")
    (root / "demo" / ".gitignore").write_text(patterns)
    original = wheel_files(root, temp_dir / "wheel")
    assert "demo/private.txt" not in original
    assert "demo/keep.txt" in original
    extracted = extract_sdist(root, temp_dir / "sdist", temp_dir / "dist", helpers)
    assert (extracted / "demo" / "private.txt").is_file()
    assert (extracted / "demo" / ".gitignore").read_text() == patterns
    assert wheel_files(extracted, temp_dir / "rebuilt") == original

    second = extract_sdist(extracted, temp_dir / "second-sdist", temp_dir / "second", helpers)
    assert wheel_files(second, temp_dir / "second-wheel") == original


def test_nested_negation_overrides_parent_rules(temp_dir):
    root = make_project(temp_dir / "pkg")
    (root / ".gitignore").write_text("*.txt\n")
    (root / "demo" / ".gitignore").write_text("!keep.txt\n")
    files = wheel_files(root, temp_dir / "wheel")
    assert "demo/keep.txt" in files
    assert "demo/private.txt" not in files


def test_ignore_vcs_disables_nested_rules(temp_dir):
    root = make_project(temp_dir / "pkg", "\n[tool.hatch.build]\nignore-vcs = true\n")
    (root / "demo" / ".gitignore").write_text("*.txt\n")
    assert "demo/private.txt" in wheel_files(root, temp_dir / "wheel")


@pytest.mark.parametrize("skip_excluded_dirs", [False, True])
@pytest.mark.parametrize("selection", ['include = ["/demo"]', 'exclude = ["/docs"]'])
def test_sdist_omits_ignore_files_for_unselected_directories(temp_dir, helpers, skip_excluded_dirs, selection):
    root = make_project(temp_dir / "pkg", f"{selection}\nskip-excluded-dirs = {str(skip_excluded_dirs).lower()}\n")
    docs = root / "docs"
    docs.mkdir()
    (docs / ".gitignore").write_text("private.txt\n")
    (docs / "private.txt").write_text("unselected data\n")

    extracted = extract_sdist(root, temp_dir / "sdist", temp_dir / "extracted", helpers)

    assert (extracted / "demo" / "__init__.py").is_file()
    assert not (extracted / "docs").exists()


@pytest.mark.parametrize("resolution", ["conflict", "identical", "force-include", "only-include"])
def test_sdist_remapped_ignore_files(temp_dir, helpers, resolution):
    selected_files = ["a/module_a.py", "b/module_b.py"]
    if resolution == "only-include":
        selected_files.append("a/.gitignore")
    config = f"only-include = {selected_files!r}\n"
    config += '[tool.hatch.build.targets.sdist.sources]\n"a" = "demo"\n"b" = "demo"\n'
    if resolution == "force-include":
        config += '[tool.hatch.build.targets.sdist.force-include]\n"../rules" = "demo/.gitignore"\n'
        (temp_dir / "rules").write_text("private-*.txt\n")
    root = make_project(temp_dir / "pkg", config)
    for directory in ("a", "b"):
        (root / directory).mkdir()
        pattern = "private-a.txt" if resolution == "identical" else f"private-{directory}.txt"
        (root / directory / ".gitignore").write_text(f".gitignore\n{pattern}\n")
        (root / directory / f"module_{directory}.py").write_text("VALUE = 1\n")

    if resolution == "conflict":
        with pytest.raises(ValueError, match="map to the same sdist path") as exc_info:
            extract_sdist(root, temp_dir / "sdist", temp_dir / "extracted", helpers)
        assert str(exc_info.value) == (
            f"Ignore files `{os.path.join('a', '.gitignore')}` and `{os.path.join('b', '.gitignore')}` "
            f"map to the same sdist path `{os.path.join('demo', '.gitignore')}` with different contents. "
            "Adjust `sources` or use `force-include` to select an ignore file for that path."
        )
        return

    extracted = extract_sdist(root, temp_dir / "sdist", temp_dir / "extracted", helpers)

    original = temp_dir / "rules" if resolution == "force-include" else root / "a" / ".gitignore"
    assert (extracted / "demo" / ".gitignore").read_bytes() == original.read_bytes()
    assert (extracted / "demo" / "module_a.py").is_file()
    assert (extracted / "demo" / "module_b.py").is_file()
