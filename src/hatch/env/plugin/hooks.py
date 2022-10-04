from typing import List, Type, Union

from hatch.env.system import SystemEnvironment
from hatch.env.virtual import VirtualEnvironment
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_environment() -> List[Union[Type[SystemEnvironment], Type[VirtualEnvironment]]]:
    return [SystemEnvironment, VirtualEnvironment]
