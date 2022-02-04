import pluggy

hookspec = pluggy.HookspecMarker('hatch')


@hookspec
def hatch_register_version_source():
    """Register new classes that adhere to the version source interface."""


@hookspec
def hatch_register_builder():
    """Register new classes that adhere to the builder interface."""


@hookspec
def hatch_register_build_hook():
    """Register new classes that adhere to the build hook interface."""


@hookspec
def hatch_register_metadata_hook():
    """Register new classes that adhere to the metadata hook interface."""
