from __future__ import annotations

from os import PathLike as _PathLike
from typing import TypeAlias

from hatch.utils.fs import Path

PathLike: TypeAlias = _PathLike[str] | Path | str
