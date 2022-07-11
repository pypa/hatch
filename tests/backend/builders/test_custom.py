import re
import zipfile

import pytest

from hatchling.builders.custom import CustomBuilder
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT


def test_target_config_not_table(isolation):
    config = {'tool': {'hatch': {'build': {'targets': {'custom': 9000}}}}}

    with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.custom` must be a table'):
        CustomBuilder(str(isolation), config=config)


def test_no_path(isolation):
    config = {
        'tool': {
            'hatch': {
                'build': {'targets': {'custom': {'path': ''}}},
            },
        },
    }

    with pytest.raises(ValueError, match='Option `path` for builder `custom` must not be empty if defined'):
        CustomBuilder(str(isolation), config=config)


def test_path_not_string(isolation):
    config = {'tool': {'hatch': {'build': {'targets': {'custom': {'path': 3}}}}}}

    with pytest.raises(TypeError, match='Option `path` for builder `custom` must be a string'):
        CustomBuilder(str(isolation), config=config)


def test_nonexistent(isolation):
    config = {'tool': {'hatch': {'build': {'targets': {'custom': {'path': 'test.py'}}}}}}

    with pytest.raises(OSError, match='Build script does not exist: test.py'):
        CustomBuilder(str(isolation), config=config)


def test_default(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    config = {
        'project': {'name': project_name, 'dynamic': ['version']},
        'tool': {
            'hatch': {
                'version': {'path': 'my_app/__about__.py'},
                'build': {'targets': {'custom': {}}},
            },
        },
    }

    file_path = project_path / DEFAULT_BUILD_SCRIPT
    file_path.write_text(
        helpers.dedent(
            """
            import os

            from hatchling.builders.wheel import WheelBuilder

            def get_builder():
                return CustomWheelBuilder

            class CustomWheelBuilder(WheelBuilder):
                def build(self, *args, **kwargs):
                    for i, artifact in enumerate(super().build(*args, **kwargs)):
                        build_dir = os.path.dirname(artifact)
                        new_path = os.path.join(build_dir, f'{self.PLUGIN_NAME}-{i}.whl')
                        os.replace(artifact, new_path)
                        yield new_path
            """
        )
    )
    builder = CustomBuilder(str(project_path), config=config)

    build_path = project_path / 'dist'

    with project_path.as_cwd():
        artifacts = list(builder.build())

    assert len(artifacts) == 1
    expected_artifact = artifacts[0]

    build_artifacts = list(build_path.iterdir())
    assert len(build_artifacts) == 1
    assert expected_artifact == str(build_artifacts[0])
    assert expected_artifact == str(build_path / 'custom-0.whl')

    extraction_directory = temp_dir / '_archive'
    extraction_directory.mkdir()

    with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
        zip_archive.extractall(str(extraction_directory))

    metadata_directory = f'{builder.project_id}.dist-info'
    expected_files = helpers.get_template_files(
        'wheel.standard_default_license_single', project_name, metadata_directory=metadata_directory
    )
    helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    # Inspect the archive rather than the extracted files because on Windows they lose their metadata
    # https://stackoverflow.com/q/9813243
    with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
        zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
        assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)


def test_explicit_path(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    config = {
        'project': {'name': project_name, 'dynamic': ['version']},
        'tool': {
            'hatch': {
                'version': {'path': 'my_app/__about__.py'},
                'build': {'targets': {'custom': {'path': f'foo/{DEFAULT_BUILD_SCRIPT}'}}},
            },
        },
    }

    file_path = project_path / 'foo' / DEFAULT_BUILD_SCRIPT
    file_path.ensure_parent_dir_exists()
    file_path.write_text(
        helpers.dedent(
            """
            import os

            from hatchling.builders.wheel import WheelBuilder

            def get_builder():
                return CustomWheelBuilder

            class CustomWheelBuilder(WheelBuilder):
                def build(self, *args, **kwargs):
                    for i, artifact in enumerate(super().build(*args, **kwargs)):
                        build_dir = os.path.dirname(artifact)
                        new_path = os.path.join(build_dir, f'{self.PLUGIN_NAME}-{i}.whl')
                        os.replace(artifact, new_path)
                        yield new_path
            """
        )
    )
    builder = CustomBuilder(str(project_path), config=config)

    build_path = project_path / 'dist'

    with project_path.as_cwd():
        artifacts = list(builder.build())

    assert len(artifacts) == 1
    expected_artifact = artifacts[0]

    build_artifacts = list(build_path.iterdir())
    assert len(build_artifacts) == 1
    assert expected_artifact == str(build_artifacts[0])
    assert expected_artifact == str(build_path / 'custom-0.whl')

    extraction_directory = temp_dir / '_archive'
    extraction_directory.mkdir()

    with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
        zip_archive.extractall(str(extraction_directory))

    metadata_directory = f'{builder.project_id}.dist-info'
    expected_files = helpers.get_template_files(
        'wheel.standard_default_license_single', project_name, metadata_directory=metadata_directory
    )
    helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    # Inspect the archive rather than the extracted files because on Windows they lose their metadata
    # https://stackoverflow.com/q/9813243
    with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
        zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
        assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)


def test_no_subclass(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    config = {
        'project': {'name': project_name, 'dynamic': ['version']},
        'tool': {
            'hatch': {
                'version': {'path': 'my_app/__about__.py'},
                'build': {'targets': {'custom': {'path': f'foo/{DEFAULT_BUILD_SCRIPT}'}}},
            },
        },
    }

    file_path = project_path / 'foo' / DEFAULT_BUILD_SCRIPT
    file_path.ensure_parent_dir_exists()
    file_path.write_text(
        helpers.dedent(
            """
            from hatchling.builders.plugin.interface import BuilderInterface

            foo = None
            bar = 'baz'

            class CustomBuilder:
                pass
            """
        )
    )

    with pytest.raises(
        ValueError,
        match=re.escape(f'Unable to find a subclass of `BuilderInterface` in `foo/{DEFAULT_BUILD_SCRIPT}`: {temp_dir}'),
    ):
        with project_path.as_cwd():
            CustomBuilder(str(project_path), config=config)


def test_multiple_subclasses(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    config = {
        'project': {'name': project_name, 'dynamic': ['version']},
        'tool': {
            'hatch': {
                'version': {'path': 'my_app/__about__.py'},
                'build': {'targets': {'custom': {'path': f'foo/{DEFAULT_BUILD_SCRIPT}'}}},
            },
        },
    }

    file_path = project_path / 'foo' / DEFAULT_BUILD_SCRIPT
    file_path.ensure_parent_dir_exists()
    file_path.write_text(
        helpers.dedent(
            """
            import os

            from hatchling.builders.wheel import WheelBuilder

            class CustomWheelBuilder(WheelBuilder):
                pass
            """
        )
    )

    with pytest.raises(
        ValueError,
        match=re.escape(
            f'Multiple subclasses of `BuilderInterface` found in `foo/{DEFAULT_BUILD_SCRIPT}`, select '
            f'one by defining a function named `get_builder`: {temp_dir}'
        ),
    ):
        with project_path.as_cwd():
            CustomBuilder(str(project_path), config=config)
