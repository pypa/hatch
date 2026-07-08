from __future__ import annotations

import typing

from hatchling.builders.hooks.custom import CustomBuildHook
from hatchling.builders.hooks.version import VersionBuildHook
from hatchling.plugin import hookimpl

if typing.TYPE_CHECKING:
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface


@hookimpl
def hatch_register_build_hook() -> list[type[BuildHookInterface]]:
    return [CustomBuildHook, VersionBuildHook]  # type: ignore[list-item]
