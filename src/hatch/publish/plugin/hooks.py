from hatch.publish.index import IndexPublisher
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_publisher():
    return IndexPublisher
