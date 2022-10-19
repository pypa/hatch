from __future__ import annotations

from hatch.template.default import DefaultTemplate
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_template() -> type[DefaultTemplate]:
    return DefaultTemplate
