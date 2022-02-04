import os


def get_requires_for_build_sdist(config_settings=None):
    """
    https://www.python.org/dev/peps/pep-0517/#get-requires-for-build-sdist
    """
    from .builders.sdist import SdistBuilder

    builder = SdistBuilder(os.getcwd())
    return builder.config.dependencies


def build_sdist(sdist_directory, config_settings=None):
    """
    https://www.python.org/dev/peps/pep-0517/#build-sdist
    """
    from .builders.sdist import SdistBuilder

    builder = SdistBuilder(os.getcwd())
    return os.path.basename(next(builder.build(sdist_directory, ['standard'])))


def get_requires_for_build_wheel(config_settings=None):
    """
    https://www.python.org/dev/peps/pep-0517/#get-requires-for-build-wheel
    """
    from .builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd())
    return builder.config.dependencies


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """
    https://www.python.org/dev/peps/pep-0517/#build-wheel
    """
    from .builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd())
    return os.path.basename(next(builder.build(wheel_directory, ['standard'])))


def get_requires_for_build_editable(config_settings=None):
    """
    https://www.python.org/dev/peps/pep-0660/#get-requires-for-build-editable
    """
    from .builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd())
    return builder.config.dependencies


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    """
    https://www.python.org/dev/peps/pep-0660/#build-editable
    """
    from .builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd())
    return os.path.basename(next(builder.build(wheel_directory, ['editable'])))
