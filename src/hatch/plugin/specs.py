from hatchling.plugin.specs import hookspec


@hookspec
def hatch_register_environment():
    """Register new classes that adhere to the environment interface."""


@hookspec
def hatch_register_environment_collector():
    """Register new classes that adhere to the environment collector interface."""


@hookspec
def hatch_register_version_scheme():
    """Register new classes that adhere to the version scheme interface."""


@hookspec
def hatch_register_publisher():
    """Register new classes that adhere to the publisher interface."""


@hookspec
def hatch_register_template():
    """Register new classes that adhere to the template interface."""
