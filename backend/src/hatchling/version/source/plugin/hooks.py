from __future__ import annotations

from hatchling.plugin import hookimpl
from hatchling.version.source.code import CodeSource
from hatchling.version.source.env import EnvSource
from hatchling.version.source.regex import RegexSource


@hookimpl
def hatch_register_version_source() -> list[type[CodeSource] | type[EnvSource] | type[RegexSource]]:
    return [CodeSource, EnvSource, RegexSource]
