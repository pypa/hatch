from __future__ import annotations

from typing import TYPE_CHECKING

from hatchling.metadata.custom import CustomMetadataHook
from hatchling.plugin import hookimpl

if TYPE_CHECKING:
    from hatchling.metadata.plugin.interface import MetadataHookInterface


@hookimpl
def hatch_register_metadata_hook() -> type[MetadataHookInterface]:
    return CustomMetadataHook  # type: ignore[return-value]
