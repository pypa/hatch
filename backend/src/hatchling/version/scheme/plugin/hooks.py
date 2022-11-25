from __future__ import annotations

from typing import TYPE_CHECKING

from hatchling.plugin import hookimpl
from hatchling.version.scheme.standard import StandardScheme

if TYPE_CHECKING:
    from hatchling.version.scheme.plugin.interface import VersionSchemeInterface


@hookimpl
def hatch_register_version_scheme() -> type[VersionSchemeInterface]:
    return StandardScheme
