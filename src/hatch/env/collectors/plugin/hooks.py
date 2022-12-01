from hatch.env.collectors.custom import CustomEnvironmentCollector
from hatch.env.collectors.default import DefaultEnvironmentCollector
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_environment_collector():
    return [CustomEnvironmentCollector, DefaultEnvironmentCollector]
