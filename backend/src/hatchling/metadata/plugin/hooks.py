from hatchling.metadata.custom import CustomMetadataHook
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_metadata_hook():
    return CustomMetadataHook
