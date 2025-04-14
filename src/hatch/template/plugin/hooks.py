from __future__ import annotations

from typing import TYPE_CHECKING

from hatch.template.default import DefaultTemplate
from hatchling.plugin import hookimpl

if TYPE_CHECKING:
    from hatch.template.plugin.interface import TemplateInterface


@hookimpl
def hatch_register_template() -> type[TemplateInterface]:
    return DefaultTemplate
