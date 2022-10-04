import pluggy

hookspec = pluggy.HookspecMarker('hatch')


@hookspec
def hatch_register_version_source() -> None:
    """Register new classes that adhere to the version source interface."""


@hookspec
def hatch_register_builder() -> None:
    """Register new classes that adhere to the builder interface."""


@hookspec
def hatch_register_build_hook() -> None:
    """Register new classes that adhere to the build hook interface."""


@hookspec
def hatch_register_metadata_hook() -> None:
    """Register new classes that adhere to the metadata hook interface."""
