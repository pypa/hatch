from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hatch.utils.fs import Path


class File:
    def __init__(self, path: Path | None, contents: str = ''):
        self.path = path
        self.contents = contents
        self.feature = None

    def write(self, root):
        if self.path is None:  # no cov
            return

        path = root / self.path
        path.ensure_parent_dir_exists()
        path.write_text(self.contents, encoding='utf-8')


def find_template_files(module):
    for name in dir(module):
        obj = getattr(module, name)
        if obj is File:
            continue

        with suppress(TypeError):
            if issubclass(obj, File):
                yield obj
