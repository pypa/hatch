from ...plugin import hookimpl
from ..custom import CustomBuilder
from ..sdist import SdistBuilder
from ..wheel import WheelBuilder


@hookimpl
def hatch_register_builder():
    return [CustomBuilder, SdistBuilder, WheelBuilder]
