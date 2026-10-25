from __future__ import annotations

import os
import tarfile
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator


def unpack_sdist(sdist_path: str, destination: str) -> str:
    """Extract a gzipped sdist and return the path to its single top-level directory."""
    with tarfile.open(sdist_path, "r:gz") as archive:
        archive.extractall(destination, filter="data")

    children = [os.path.join(destination, name) for name in os.listdir(destination)]
    if len(children) != 1 or not os.path.isdir(children[0]):
        message = f"Expected a single top-level directory in sdist `{sdist_path}`, found {len(children)} entries"
        raise RuntimeError(message)

    return children[0]


def build_wheel_from_sdist(
    *,
    sdist_path: str,
    wheel_builder_class: type,
    plugin_manager,
    app,
    directory: str | None,
    versions: list[str],
    hooks_only: bool,
    clean: bool,
    clean_hooks_after: bool,
    clean_only: bool,
) -> Generator[str, None, None]:
    """Build a wheel using the contents of an sdist as the project root."""
    with TemporaryDirectory() as temp_dir:
        project_root = unpack_sdist(sdist_path, temp_dir)
        builder = wheel_builder_class(
            project_root,
            plugin_manager=plugin_manager,
            app=app,
        )
        yield from builder.build(
            directory=directory,
            versions=versions,
            hooks_only=hooks_only,
            clean=clean,
            clean_hooks_after=clean_hooks_after,
            clean_only=clean_only,
        )
