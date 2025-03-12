from hatchling.plugin.specs import hookspec


@hookspec
def hatch_register_environment() -> None:
    """Register new classes that adhere to the environment interface."""


@hookspec
def hatch_register_environment_collector() -> None:
    """Register new classes that adhere to the environment collector interface."""


@hookspec
def hatch_register_version_scheme() -> None:
    """Register new classes that adhere to the version scheme interface."""


@hookspec
def hatch_register_publisher() -> None:
    """Register new classes that adhere to the publisher interface."""


@hookspec
def hatch_register_template() -> None:
    """Register new classes that adhere to the template interface."""
