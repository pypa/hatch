from __future__ import annotations

from hatch.env.collectors.default import DefaultEnvironmentCollector
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_environment_collector() -> type[DefaultEnvironmentCollector]:
    return DefaultEnvironmentCollector
