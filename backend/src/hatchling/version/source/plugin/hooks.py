from ....plugin import hookimpl
from ..regex import RegexSource


@hookimpl
def hatch_register_version_source():
    return RegexSource
