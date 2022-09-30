from typing import Type

from hatch.template.default import DefaultTemplate
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_template() -> Type[DefaultTemplate]:
    return DefaultTemplate
