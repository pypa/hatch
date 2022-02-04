from hatchling.plugin import hookimpl

from ..default import DefaultEnvironmentCollector


@hookimpl
def hatch_register_environment_collector():
    return DefaultEnvironmentCollector
