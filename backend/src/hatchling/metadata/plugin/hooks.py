from __future__ import annotations

from hatchling.metadata.custom import CustomMetadataHook
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_metadata_hook() -> type[CustomMetadataHook]:
    return CustomMetadataHook
