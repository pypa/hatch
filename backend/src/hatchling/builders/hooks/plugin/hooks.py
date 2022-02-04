from ....plugin import hookimpl
from ..custom import CustomBuildHook


@hookimpl
def hatch_register_build_hook():
    return CustomBuildHook
