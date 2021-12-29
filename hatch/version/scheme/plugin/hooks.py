from hatchling.plugin import hookimpl

from ..standard import StandardScheme


@hookimpl
def hatch_register_version_scheme():
    return StandardScheme
