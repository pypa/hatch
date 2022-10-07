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


# Any builder that has build-time hooks like Hatchling and setuptools cannot technically keep PEP 517's identical
# metadata promise e.g. C extensions would require different tags in the `WHEEL` file. Therefore, we consider the
# methods as mostly being for non-frontend tools like tox and dependency updaters. So Hatchling only writes the
# `METADATA` file to the metadata directory and continues to ignore that directory itself.
#
# An issue we encounter by supporting this metadata-only access is that for installations with pip the required
# dependencies of the project are read at this stage. This means that build hooks that add to the `dependencies`
# build data or modify the built wheel have no effect on what dependencies are or are not installed.
#
# There are legitimate use cases in which this is required, so we only define these when no pip build is detected.
# See: https://github.com/pypa/pip/blob/22.2.2/src/pip/_internal/operations/build/build_tracker.py#L41-L51
# Example use case: https://github.com/pypa/hatch/issues/532
if 'PIP_BUILD_TRACKER' not in os.environ:

    def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
        """
        https://peps.python.org/pep-0517/#prepare-metadata-for-build-wheel
        """
        from hatchling.builders.wheel import WheelBuilder

        builder = WheelBuilder(os.getcwd())

        directory = os.path.join(metadata_directory, f'{builder.artifact_project_id}.dist-info')
        if not os.path.isdir(directory):
            os.mkdir(directory)

        with open(os.path.join(directory, 'METADATA'), 'w', encoding='utf-8') as f:
            f.write(builder.config.core_metadata_constructor(builder.metadata))

        return os.path.basename(directory)

    def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
        """
        https://peps.python.org/pep-0660/#prepare-metadata-for-build-editable
        """
        from hatchling.builders.wheel import EDITABLES_MINIMUM_VERSION, WheelBuilder

        builder = WheelBuilder(os.getcwd())

        directory = os.path.join(metadata_directory, f'{builder.artifact_project_id}.dist-info')
        if not os.path.isdir(directory):
            os.mkdir(directory)

        extra_dependencies = []
        if not builder.config.dev_mode_dirs and builder.config.dev_mode_exact:
            extra_dependencies.append(f'editables~={EDITABLES_MINIMUM_VERSION}')

        with open(os.path.join(directory, 'METADATA'), 'w', encoding='utf-8') as f:
            f.write(builder.config.core_metadata_constructor(builder.metadata, extra_dependencies=extra_dependencies))

        return os.path.basename(directory)
