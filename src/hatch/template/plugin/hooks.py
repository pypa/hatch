from hatchling.plugin import hookimpl

from ..default import DefaultTemplate


@hookimpl
def hatch_register_template():
    return DefaultTemplate
