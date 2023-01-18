from __future__ import annotations

from typing import TYPE_CHECKING

from hatch.publish.index import IndexPublisher
from hatchling.plugin import hookimpl

if TYPE_CHECKING:
    from hatch.publish.plugin.interface import PublisherInterface


@hookimpl
def hatch_register_publisher() -> type[PublisherInterface]:
    return IndexPublisher
