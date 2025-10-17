from hatchling.plugin.specs import hookspec


@hookspec
def hatch_register_environment():
    """
    DEPRECATED: Register new classes that adhere to the environment interface.

    This hook-based registration is deprecated. Use direct entrypoint groups instead:
    [project.entry-points."hatch.environment"]
    myplug = "my_package.plugin:MyEnvironment"

    See https://hatch.pypa.io/latest/plugins/about/ for migration guide.
    """


@hookspec
def hatch_register_environment_collector():
    """
    DEPRECATED: Register new classes that adhere to the environment collector interface.

    This hook-based registration is deprecated. Use direct entrypoint groups instead:
    [project.entry-points."hatch.environment_collector"]
    myplug = "my_package.plugin:MyCollector"

    See https://hatch.pypa.io/latest/plugins/about/ for migration guide.
    """


@hookspec
def hatch_register_version_scheme():
    """
    DEPRECATED: Register new classes that adhere to the version scheme interface.

    This hook-based registration is deprecated. Use direct entrypoint groups instead:
    [project.entry-points."hatch.version_scheme"]
    myplug = "my_package.plugin:MyVersionScheme"

    See https://hatch.pypa.io/latest/plugins/about/ for migration guide.
    """


@hookspec
def hatch_register_publisher():
    """
    DEPRECATED: Register new classes that adhere to the publisher interface.

    This hook-based registration is deprecated. Use direct entrypoint groups instead:
    [project.entry-points."hatch.publisher"]
    myplug = "my_package.plugin:MyPublisher"

    See https://hatch.pypa.io/latest/plugins/about/ for migration guide.
    """


@hookspec
def hatch_register_template():
    """
    DEPRECATED: Register new classes that adhere to the template interface.

    This hook-based registration is deprecated. Use direct entrypoint groups instead:
    [project.entry-points."hatch.template"]
    myplug = "my_package.plugin:MyTemplate"

    See https://hatch.pypa.io/latest/plugins/about/ for migration guide.
    """
