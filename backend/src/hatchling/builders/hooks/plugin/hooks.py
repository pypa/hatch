from __future__ import annotations

from hatchling.builders.hooks.custom import CustomBuildHook
from hatchling.builders.hooks.version import VersionBuildHook
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_build_hook() -> list[type[CustomBuildHook] | type[VersionBuildHook]]:
    return [CustomBuildHook, VersionBuildHook]
