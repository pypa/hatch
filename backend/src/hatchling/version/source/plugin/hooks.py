from hatchling.plugin import hookimpl
from hatchling.version.source.code import CodeSource
from hatchling.version.source.env import EnvSource
from hatchling.version.source.regex import RegexSource


@hookimpl
def hatch_register_version_source():
    return [CodeSource, EnvSource, RegexSource]
