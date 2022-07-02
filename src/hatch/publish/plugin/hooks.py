from hatch.publish.pypi import PyPIPublisher
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_publisher():
    return PyPIPublisher
