from __future__ import annotations

from typing import TYPE_CHECKING

from hatchling.plugin import hookimpl
from hatchling.version.source.code import CodeSource
from hatchling.version.source.env import EnvSource
from hatchling.version.source.regex import RegexSource

if TYPE_CHECKING:
    from hatchling.version.source.plugin.interface import VersionSourceInterface


@hookimpl
def hatch_register_version_source() -> list[type[VersionSourceInterface]]:
    return [CodeSource, EnvSource, RegexSource]
