from ....plugin import hookimpl
from ..custom import CustomBuildHook
from ..version import VersionBuildHook


@hookimpl
def hatch_register_build_hook():
    return [CustomBuildHook, VersionBuildHook]
