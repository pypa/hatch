import os


def get_requires_for_build_sdist(config_settings=None):
    """
    https://peps.python.org/pep-0517/#get-requires-for-build-sdist
    """
    from hatchling.builders.sdist import SdistBuilder

    builder = SdistBuilder(os.getcwd())
    return builder.config.dependencies


def build_sdist(sdist_directory, config_settings=None):
    """
    https://peps.python.org/pep-0517/#build-sdist
    """
    from hatchling.builders.sdist import SdistBuilder

    builder = SdistBuilder(os.getcwd())
    return os.path.basename(next(builder.build(sdist_directory, ['standard'])))


def get_requires_for_build_wheel(config_settings=None):
    """
    https://peps.python.org/pep-0517/#get-requires-for-build-wheel
    """
    from hatchling.builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd())
    return builder.config.dependencies


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """
    https://peps.python.org/pep-0517/#build-wheel
    """
    from hatchling.builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd())
    return os.path.basename(next(builder.build(wheel_directory, ['standard'])))


def get_requires_for_build_editable(config_settings=None):
    """
    https://peps.python.org/pep-0660/#get-requires-for-build-editable
    """
    from hatchling.builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd())
    return builder.config.dependencies


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    """
    https://peps.python.org/pep-0660/#build-editable
    """
    from hatchling.builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd())
    return os.path.basename(next(builder.build(wheel_directory, ['editable'])))
