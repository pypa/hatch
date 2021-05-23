from hatchling.plugin import hookimpl

from ..pypi import PyPIPublisher


@hookimpl
def hatch_register_publisher():
    return PyPIPublisher
