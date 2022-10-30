from __future__ import annotations

from typing import Type

from hatchling.builders.custom import CustomBuilder
from hatchling.builders.sdist import SdistBuilder
from hatchling.builders.wheel import WheelBuilder
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_builder() -> list[Type[CustomBuilder] | Type[SdistBuilder] | Type[WheelBuilder]]:
    return [CustomBuilder, SdistBuilder, WheelBuilder]
