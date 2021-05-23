from ...plugin import hookimpl
from ..custom import CustomMetadataHook


@hookimpl
def hatch_register_metadata_hook():
    return CustomMetadataHook
