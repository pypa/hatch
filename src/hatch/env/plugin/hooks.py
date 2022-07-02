from hatch.env.system import SystemEnvironment
from hatch.env.virtual import VirtualEnvironment
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_environment():
    return [SystemEnvironment, VirtualEnvironment]
