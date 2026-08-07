from __future__ import annotations

from typing import TYPE_CHECKING

from hatch.env.collectors.custom import CustomEnvironmentCollector
from hatch.env.collectors.default import DefaultEnvironmentCollector
from hatchling.plugin import hookimpl

if TYPE_CHECKING:
    from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface


@hookimpl
def hatch_register_environment_collector() -> list[type[EnvironmentCollectorInterface]]:
    # CustomEnvironmentCollector fakes its type via `__new__`; it is not a real subclass
    return [CustomEnvironmentCollector, DefaultEnvironmentCollector]  # type: ignore[list-item]
