from hatchling.builders.custom import CustomBuilder
from hatchling.builders.sdist import SdistBuilder
from hatchling.builders.wheel import WheelBuilder
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_builder():
    return [CustomBuilder, SdistBuilder, WheelBuilder]
