from ....plugin import hookimpl
from ..code import CodeSource
from ..regex import RegexSource


@hookimpl
def hatch_register_version_source():
    return [CodeSource, RegexSource]
