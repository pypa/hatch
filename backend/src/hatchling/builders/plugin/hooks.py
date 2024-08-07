from __future__ import annotations

import typing

from hatchling.builders.app import AppBuilder
from hatchling.builders.binary import BinaryBuilder
from hatchling.builders.custom import CustomBuilder
from hatchling.builders.sdist import SdistBuilder
from hatchling.builders.wheel import WheelBuilder
from hatchling.plugin import hookimpl

if typing.TYPE_CHECKING:
    from hatchling.builders.plugin.interface import BuilderInterface


@hookimpl
def hatch_register_builder() -> list[type[BuilderInterface]]:
    return [AppBuilder, BinaryBuilder, CustomBuilder, SdistBuilder, WheelBuilder]  # type: ignore[list-item]
