from hatchling.plugin import hookimpl

from ..system import SystemEnvironment
from ..virtual import VirtualEnvironment


@hookimpl
def hatch_register_environment():
    return [SystemEnvironment, VirtualEnvironment]
