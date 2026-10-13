import os
from unittest.mock import patch

from hatchling.builders.utils import safe_walk


def test_safe_walk_skips_directories_removed_during_walk(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").touch()

    cache_dir = (
        tmp_path
        / ".cache"
        / "uv"
        / "builds-v0"
        / ".tmpNWUHak"
        / "lib"
        / "python3.11"
        / "site-packages"
        / "setuptools"
        / "_vendor"
        / "jaraco"
    )
    cache_dir.mkdir(parents=True)
    (cache_dir / "text.py").touch()

    vanished = os.path.normpath(str(cache_dir))
    original_stat = os.stat

    def flaky_stat(path, *args, **kwargs):
        if os.path.normpath(os.fspath(path)) == vanished:
            raise FileNotFoundError(os.fspath(path))
        return original_stat(path, *args, **kwargs)

    with patch("os.stat", side_effect=flaky_stat):
        roots = [os.path.normpath(root) for root, _, _ in safe_walk(str(tmp_path))]

    assert os.path.normpath(str(package)) in roots
    assert vanished not in roots
