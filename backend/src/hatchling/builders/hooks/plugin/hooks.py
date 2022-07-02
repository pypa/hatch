from hatchling.builders.hooks.custom import CustomBuildHook
from hatchling.builders.hooks.version import VersionBuildHook
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_build_hook():
    return [CustomBuildHook, VersionBuildHook]
