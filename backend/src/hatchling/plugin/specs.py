import pluggy

hookspec = pluggy.HookspecMarker("hatch")


@hookspec
def hatch_register_version_source() -> None:
    """
    DEPRECATED: Register new classes that adhere to the version source interface.

    This hook-based registration is deprecated. Use direct entrypoint groups instead:
    [project.entry-points."hatch.version_source"]
    myplug = "my_package.plugin:MyVersionSource"

    See https://hatch.pypa.io/latest/plugins/about/ for migration guide.
    """


@hookspec
def hatch_register_builder() -> None:
    """
    DEPRECATED: Register new classes that adhere to the builder interface.

    This hook-based registration is deprecated. Use direct entrypoint groups instead:
    [project.entry-points."hatch.builder"]
    myplug = "my_package.plugin:MyBuilder"

    See https://hatch.pypa.io/latest/plugins/about/ for migration guide.
    """


@hookspec
def hatch_register_build_hook() -> None:
    """
    DEPRECATED: Register new classes that adhere to the build hook interface.

    This hook-based registration is deprecated. Use direct entrypoint groups instead:
    [project.entry-points."hatch.build_hook"]
    myplug = "my_package.plugin:MyBuildHook"

    See https://hatch.pypa.io/latest/plugins/about/ for migration guide.
    """


@hookspec
def hatch_register_metadata_hook() -> None:
    """
    DEPRECATED: Register new classes that adhere to the metadata hook interface.

    This hook-based registration is deprecated. Use direct entrypoint groups instead:
    [project.entry-points."hatch.metadata_hook"]
    myplug = "my_package.plugin:MyMetadataHook"

    See https://hatch.pypa.io/latest/plugins/about/ for migration guide.
    """
