from typing import Type

from hatch.env.collectors.default import DefaultEnvironmentCollector
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_environment_collector() -> Type[DefaultEnvironmentCollector]:
    return DefaultEnvironmentCollector
