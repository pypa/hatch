import os
import platform
import sys
import zipfile

import pytest
from packaging.tags import sys_tags

from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.builders.utils import get_known_python_major_versions
from hatchling.builders.wheel import WheelBuilder
from hatchling.metadata.spec import DEFAULT_METADATA_VERSION, get_core_metadata_constructors
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT

# https://github.com/python/cpython/pull/26184
fixed_pathlib_resolution = pytest.mark.skipif(
    platform.system() == 'Windows' and (sys.version_info < (3, 8) or sys.implementation.name == 'pypy'),
    reason='pathlib.Path.resolve has bug on Windows',
)


def get_python_versions_tag():
    return '.'.join(f'py{major_version}' for major_version in get_known_python_major_versions())


def test_class():
    assert issubclass(WheelBuilder, BuilderInterface)


def test_default_versions(isolation):
    builder = WheelBuilder(str(isolation))

    assert builder.get_default_versions() == ['standard']


class TestDefaultFileSelection:
    def test_flat_layout(self, temp_dir):
        config = {'project': {'name': 'my-app', 'version': '0.0.1'}}
        builder = WheelBuilder(str(temp_dir), config=config)

        flat_root = temp_dir / 'my_app' / '__init__.py'
        flat_root.ensure_parent_dir_exists()
        flat_root.touch()

        src_root = temp_dir / 'src' / 'my_app' / '__init__.py'
        src_root.ensure_parent_dir_exists()
        src_root.touch()

        single_module_root = temp_dir / 'my_app.py'
        single_module_root.touch()

        namespace_root = temp_dir / 'ns' / 'my_app' / '__init__.py'
        namespace_root.ensure_parent_dir_exists()
        namespace_root.touch()

        assert builder.config.default_include() == []
        assert builder.config.default_exclude() == []
        assert builder.config.default_packages() == ['my_app']

    def test_src_layout(self, temp_dir):
        config = {'project': {'name': 'my-app', 'version': '0.0.1'}}
        builder = WheelBuilder(str(temp_dir), config=config)

        src_root = temp_dir / 'src' / 'my_app' / '__init__.py'
        src_root.ensure_parent_dir_exists()
        src_root.touch()

        single_module_root = temp_dir / 'my_app.py'
        single_module_root.touch()

        namespace_root = temp_dir / 'ns' / 'my_app' / '__init__.py'
        namespace_root.ensure_parent_dir_exists()
        namespace_root.touch()

        assert builder.config.default_include() == []
        assert builder.config.default_exclude() == []
        assert builder.config.default_packages() == ['src/my_app']

    def test_single_module(self, temp_dir):
        config = {'project': {'name': 'my-app', 'version': '0.0.1'}}
        builder = WheelBuilder(str(temp_dir), config=config)

        single_module_root = temp_dir / 'my_app.py'
        single_module_root.touch()

        namespace_root = temp_dir / 'ns' / 'my_app' / '__init__.py'
        namespace_root.ensure_parent_dir_exists()
        namespace_root.touch()

        assert builder.config.default_include() == []
        assert builder.config.default_exclude() == []
        assert builder.config.default_packages() == ['my_app.py']

    def test_namespace(self, temp_dir):
        config = {'project': {'name': 'my-app', 'version': '0.0.1'}}
        builder = WheelBuilder(str(temp_dir), config=config)

        namespace_root = temp_dir / 'ns' / 'my_app' / '__init__.py'
        namespace_root.ensure_parent_dir_exists()
        namespace_root.touch()

        assert builder.config.default_include() == []
        assert builder.config.default_exclude() == []
        assert builder.config.default_packages() == ['ns']

    def test_default(self, temp_dir):
        config = {'project': {'name': 'my-app', 'version': '0.0.1'}}
        builder = WheelBuilder(str(temp_dir), config=config)

        for i in range(2):
            namespace_root = temp_dir / f'ns{i}' / 'my_app' / '__init__.py'
            namespace_root.ensure_parent_dir_exists()
            namespace_root.touch()

        assert builder.config.default_include() == ['*.py']
        assert builder.config.default_exclude() == ['test*']
        assert builder.config.default_packages() == []

    def test_raw_name_not_normalized(self, temp_dir):
        config = {'project': {'name': 'MyApp', 'version': '0.0.1'}}
        builder = WheelBuilder(str(temp_dir), config=config)

        src_root = temp_dir / 'src' / 'MyApp' / '__init__.py'
        src_root.ensure_parent_dir_exists()
        src_root.touch()

        assert builder.config.default_packages() == ['src/MyApp']


class TestCoreMetadataConstructor:
    def test_default(self, isolation):
        builder = WheelBuilder(str(isolation))

        assert builder.config.core_metadata_constructor is builder.config.core_metadata_constructor
        assert builder.config.core_metadata_constructor is get_core_metadata_constructors()[DEFAULT_METADATA_VERSION]

    def test_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'core-metadata-version': 42}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(
            TypeError, match='Field `tool.hatch.build.targets.wheel.core-metadata-version` must be a string'
        ):
            _ = builder.config.core_metadata_constructor

    def test_unknown(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'core-metadata-version': '9000'}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(
            ValueError,
            match=(
                f'Unknown metadata version `9000` for field `tool.hatch.build.targets.wheel.core-metadata-version`. '
                f'Available: {", ".join(sorted(get_core_metadata_constructors()))}'
            ),
        ):
            _ = builder.config.core_metadata_constructor


class TestSharedData:
    def test_default(self, isolation):
        builder = WheelBuilder(str(isolation))

        assert builder.config.shared_data == builder.config.shared_data == {}

    def test_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'shared-data': 42}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.wheel.shared-data` must be a mapping'):
            _ = builder.config.shared_data

    def test_absolute(self, isolation):
        config = {
            'tool': {
                'hatch': {'build': {'targets': {'wheel': {'shared-data': {str(isolation / 'source'): '/target/'}}}}}
            }
        }
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.config.shared_data == {str(isolation / 'source'): 'target'}

    def test_relative(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'shared-data': {'../source': '/target/'}}}}}}}
        builder = WheelBuilder(str(isolation / 'foo'), config=config)

        assert builder.config.shared_data == {str(isolation / 'source'): 'target'}

    def test_source_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'shared-data': {'': '/target/'}}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(
            ValueError,
            match='Source #1 in field `tool.hatch.build.targets.wheel.shared-data` cannot be an empty string',
        ):
            _ = builder.config.shared_data

    def test_relative_path_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'shared-data': {'source': 0}}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(
            TypeError,
            match='Path for source `source` in field `tool.hatch.build.targets.wheel.shared-data` must be a string',
        ):
            _ = builder.config.shared_data

    def test_relative_path_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'shared-data': {'source': ''}}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(
            ValueError,
            match=(
                'Path for source `source` in field `tool.hatch.build.targets.wheel.shared-data` '
                'cannot be an empty string'
            ),
        ):
            _ = builder.config.shared_data

    def test_order(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'targets': {
                            'wheel': {
                                'shared-data': {
                                    '../very-nested': 'target1/embedded',
                                    '../source1': '/target2/',
                                    '../source2': '/target1/',
                                }
                            }
                        }
                    }
                }
            }
        }
        builder = WheelBuilder(str(isolation / 'foo'), config=config)

        assert builder.config.shared_data == {
            str(isolation / 'source2'): 'target1',
            str(isolation / 'very-nested'): f'target1{os.sep}embedded',
            str(isolation / 'source1'): 'target2',
        }


class TestExtraMetadata:
    def test_default(self, isolation):
        builder = WheelBuilder(str(isolation))

        assert builder.config.extra_metadata == builder.config.extra_metadata == {}

    def test_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'extra-metadata': 42}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.wheel.extra-metadata` must be a mapping'):
            _ = builder.config.extra_metadata

    def test_absolute(self, isolation):
        config = {
            'tool': {
                'hatch': {'build': {'targets': {'wheel': {'extra-metadata': {str(isolation / 'source'): '/target/'}}}}}
            }
        }
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.config.extra_metadata == {str(isolation / 'source'): 'target'}

    def test_relative(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'extra-metadata': {'../source': '/target/'}}}}}}}
        builder = WheelBuilder(str(isolation / 'foo'), config=config)

        assert builder.config.extra_metadata == {str(isolation / 'source'): 'target'}

    def test_source_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'extra-metadata': {'': '/target/'}}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(
            ValueError,
            match='Source #1 in field `tool.hatch.build.targets.wheel.extra-metadata` cannot be an empty string',
        ):
            _ = builder.config.extra_metadata

    def test_relative_path_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'extra-metadata': {'source': 0}}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(
            TypeError,
            match='Path for source `source` in field `tool.hatch.build.targets.wheel.extra-metadata` must be a string',
        ):
            _ = builder.config.extra_metadata

    def test_relative_path_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'extra-metadata': {'source': ''}}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(
            ValueError,
            match=(
                'Path for source `source` in field `tool.hatch.build.targets.wheel.extra-metadata` '
                'cannot be an empty string'
            ),
        ):
            _ = builder.config.extra_metadata

    def test_order(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'targets': {
                            'wheel': {
                                'extra-metadata': {
                                    '../very-nested': 'target1/embedded',
                                    '../source1': '/target2/',
                                    '../source2': '/target1/',
                                }
                            }
                        }
                    }
                }
            }
        }
        builder = WheelBuilder(str(isolation / 'foo'), config=config)

        assert builder.config.extra_metadata == {
            str(isolation / 'source2'): 'target1',
            str(isolation / 'very-nested'): f'target1{os.sep}embedded',
            str(isolation / 'source1'): 'target2',
        }


class TestStrictNaming:
    def test_default(self, isolation):
        builder = WheelBuilder(str(isolation))

        assert builder.config.strict_naming is builder.config.strict_naming is True

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'strict-naming': False}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.config.strict_naming is False

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'strict-naming': 9000}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.wheel.strict-naming` must be a boolean'):
            _ = builder.config.strict_naming

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'strict-naming': False}}}}
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.config.strict_naming is False

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'strict-naming': 9000}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.strict-naming` must be a boolean'):
            _ = builder.config.strict_naming

    def test_target_overrides_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'strict-naming': False, 'targets': {'wheel': {'strict-naming': True}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.config.strict_naming is True


class TestConstructEntryPointsFile:
    def test_default(self, isolation):
        config = {'project': {}}
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.construct_entry_points_file() == ''

    def test_scripts(self, isolation, helpers):
        config = {'project': {'scripts': {'foo': 'pkg:bar', 'bar': 'pkg:foo'}}}
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.construct_entry_points_file() == helpers.dedent(
            """
            [console_scripts]
            bar = pkg:foo
            foo = pkg:bar
            """
        )

    def test_gui_scripts(self, isolation, helpers):
        config = {'project': {'gui-scripts': {'foo': 'pkg:bar', 'bar': 'pkg:foo'}}}
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.construct_entry_points_file() == helpers.dedent(
            """
            [gui_scripts]
            bar = pkg:foo
            foo = pkg:bar
            """
        )

    def test_entry_points(self, isolation, helpers):
        config = {
            'project': {
                'entry-points': {
                    'foo': {'bar': 'pkg:foo', 'foo': 'pkg:bar'},
                    'bar': {'foo': 'pkg:bar', 'bar': 'pkg:foo'},
                }
            }
        }
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.construct_entry_points_file() == helpers.dedent(
            """
            [bar]
            bar = pkg:foo
            foo = pkg:bar

            [foo]
            bar = pkg:foo
            foo = pkg:bar
            """
        )

    def test_all(self, isolation, helpers):
        config = {
            'project': {
                'scripts': {'foo': 'pkg:bar', 'bar': 'pkg:foo'},
                'gui-scripts': {'foo': 'pkg:bar', 'bar': 'pkg:foo'},
                'entry-points': {
                    'foo': {'bar': 'pkg:foo', 'foo': 'pkg:bar'},
                    'bar': {'foo': 'pkg:bar', 'bar': 'pkg:foo'},
                },
            }
        }
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.construct_entry_points_file() == helpers.dedent(
            """
            [console_scripts]
            bar = pkg:foo
            foo = pkg:bar

            [gui_scripts]
            bar = pkg:foo
            foo = pkg:bar

            [bar]
            bar = pkg:foo
            foo = pkg:bar

            [foo]
            bar = pkg:foo
            foo = pkg:bar
            """
        )


class TestBuildStandard:
    def test_default_auto_detection(self, hatch, helpers, temp_dir):
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
                    'build': {'targets': {'wheel': {'versions': ['standard']}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

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

    def test_default_reproducible_timestamp(self, hatch, helpers, temp_dir):
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
                    'build': {'targets': {'wheel': {'versions': ['standard']}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd(env_vars={'SOURCE_DATE_EPOCH': '1580601700'}):
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_license_single', project_name, metadata_directory=metadata_directory
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 1, 40)

    def test_default_no_reproducible(self, hatch, helpers, temp_dir):
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
                    'build': {'targets': {'wheel': {'versions': ['standard'], 'reproducible': False}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd(env_vars={'SOURCE_DATE_EPOCH': '1580601700'}):
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_license_single', project_name, metadata_directory=metadata_directory
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    def test_default_multiple_licenses(self, hatch, helpers, config_file, temp_dir):
        project_name = 'My.App'
        config_file.model.template.licenses.default = ['MIT', 'Apache-2.0']
        config_file.save()

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        # Ensure that we trigger the non-file case for code coverage
        (project_path / 'LICENSES' / 'test').mkdir()

        config = {
            'project': {'name': project_name, 'dynamic': ['version'], 'license-files': {'globs': ['LICENSES/*']}},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {'targets': {'wheel': {'versions': ['standard']}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_license_multiple', project_name, metadata_directory=metadata_directory
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_include(self, hatch, helpers, temp_dir):
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
                    'build': {'targets': {'wheel': {'versions': ['standard'], 'include': ['my_app', 'tests']}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_tests', project_name, metadata_directory=metadata_directory
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_only_packages(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        tests_path = project_path / 'tests'
        (tests_path / '__init__.py').replace(tests_path / 'foo.py')

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {
                            'wheel': {'versions': ['standard'], 'include': ['my_app', 'tests'], 'only-packages': True}
                        },
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_license_single', project_name, metadata_directory=metadata_directory
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_only_packages_artifact_override(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        tests_path = project_path / 'tests'
        (tests_path / '__init__.py').replace(tests_path / 'foo.py')

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'artifacts': ['foo.py'],
                        'targets': {
                            'wheel': {'versions': ['standard'], 'include': ['my_app', 'tests'], 'only-packages': True}
                        },
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_only_packages_artifact_override', project_name, metadata_directory=metadata_directory
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_python_constraint(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {'targets': {'wheel': {'versions': ['standard']}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-py3-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_python_constraint', project_name, metadata_directory=metadata_directory
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_build_script_default_tag(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    pass
                """
            )
        )

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'hooks': {'custom': {'path': DEFAULT_BUILD_SCRIPT}},
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        tag = 'py3-none-any'
        assert expected_artifact == str(build_path / f'{builder.project_id}-{tag}.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_build_script', project_name, metadata_directory=metadata_directory, tag=tag
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_build_script_set_tag(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['tag'] = 'foo-bar-baz'
                """
            )
        )

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'hooks': {'custom': {'path': DEFAULT_BUILD_SCRIPT}},
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        tag = 'foo-bar-baz'
        assert expected_artifact == str(build_path / f'{builder.project_id}-{tag}.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_build_script', project_name, metadata_directory=metadata_directory, tag=tag
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_build_script_known_artifacts(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.h')

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['pure_python'] = False
                        build_data['infer_tag'] = True

                        pathlib.Path('my_app', 'lib.so').touch()
                        pathlib.Path('my_app', 'lib.h').touch()
                """
            )
        )

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'artifacts': ['my_app/lib.so'],
                        'hooks': {'custom': {'path': DEFAULT_BUILD_SCRIPT}},
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        best_matching_tag = next(sys_tags())
        tag = f'{best_matching_tag.interpreter}-{best_matching_tag.abi}-{best_matching_tag.platform}'
        assert expected_artifact == str(build_path / f'{builder.project_id}-{tag}.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_build_script_artifacts',
            project_name,
            metadata_directory=metadata_directory,
            tag=tag,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_build_script_configured_build_hooks(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.h')

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['pure_python'] = False
                        build_data['infer_tag'] = True

                        pathlib.Path('my_app', 'lib.so').write_text(','.join(build_data['build_hooks']))
                        pathlib.Path('my_app', 'lib.h').write_text(','.join(build_data['build_hooks']))
                """
            )
        )

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'artifacts': ['my_app/lib.so'],
                        'hooks': {'custom': {'path': DEFAULT_BUILD_SCRIPT}},
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        best_matching_tag = next(sys_tags())
        tag = f'{best_matching_tag.interpreter}-{best_matching_tag.abi}-{best_matching_tag.platform}'
        assert expected_artifact == str(build_path / f'{builder.project_id}-{tag}.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_build_script_configured_build_hooks',
            project_name,
            metadata_directory=metadata_directory,
            tag=tag,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_build_script_extra_dependencies(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.h')

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['pure_python'] = False
                        build_data['infer_tag'] = True
                        build_data['dependencies'].append('binary')

                        pathlib.Path('my_app', 'lib.so').touch()
                        pathlib.Path('my_app', 'lib.h').touch()
                """
            )
        )

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'artifacts': ['my_app/lib.so'],
                        'hooks': {'custom': {'path': DEFAULT_BUILD_SCRIPT}},
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        best_matching_tag = next(sys_tags())
        tag = f'{best_matching_tag.interpreter}-{best_matching_tag.abi}-{best_matching_tag.platform}'
        assert expected_artifact == str(build_path / f'{builder.project_id}-{tag}.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_build_script_extra_dependencies',
            project_name,
            metadata_directory=metadata_directory,
            tag=tag,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_build_script_dynamic_artifacts(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.h')

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['pure_python'] = False
                        build_data['infer_tag'] = True
                        build_data['artifacts'] = ['my_app/lib.so']

                        pathlib.Path('my_app', 'lib.so').touch()
                        pathlib.Path('my_app', 'lib.h').touch()
                """
            )
        )

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'hooks': {'custom': {'path': DEFAULT_BUILD_SCRIPT}},
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        best_matching_tag = next(sys_tags())
        tag = f'{best_matching_tag.interpreter}-{best_matching_tag.abi}-{best_matching_tag.platform}'
        assert expected_artifact == str(build_path / f'{builder.project_id}-{tag}.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_build_script_artifacts',
            project_name,
            metadata_directory=metadata_directory,
            tag=tag,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_build_script_dynamic_force_include(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.h')

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['pure_python'] = False
                        build_data['infer_tag'] = True
                        build_data['artifacts'].extend(('lib.so', 'lib.h'))
                        build_data['force_include']['../artifacts'] = 'my_app'

                        artifact_path = pathlib.Path('..', 'artifacts')
                        artifact_path.mkdir()
                        (artifact_path / 'lib.so').touch()
                        (artifact_path / 'lib.h').touch()
                """
            )
        )

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'hooks': {'custom': {'path': DEFAULT_BUILD_SCRIPT}},
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        best_matching_tag = next(sys_tags())
        tag = f'{best_matching_tag.interpreter}-{best_matching_tag.abi}-{best_matching_tag.platform}'
        assert expected_artifact == str(build_path / f'{builder.project_id}-{tag}.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_build_script_force_include',
            project_name,
            metadata_directory=metadata_directory,
            tag=tag,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_build_script_dynamic_artifacts_with_src_layout(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['src-layout'] = True
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.pyd\n*.h')

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['pure_python'] = False
                        build_data['infer_tag'] = True
                        build_data['artifacts'] = ['src/my_app/lib.so']
                        build_data['force_include']['src/zlib.pyd'] = 'src/zlib.pyd'

                        pathlib.Path('src', 'my_app', 'lib.so').touch()
                        pathlib.Path('src', 'lib.h').touch()
                        pathlib.Path('src', 'zlib.pyd').touch()
                """
            )
        )

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'src/my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'hooks': {'custom': {'path': DEFAULT_BUILD_SCRIPT}},
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        best_matching_tag = next(sys_tags())
        tag = f'{best_matching_tag.interpreter}-{best_matching_tag.abi}-{best_matching_tag.platform}'
        assert expected_artifact == str(build_path / f'{builder.project_id}-{tag}.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_build_script_artifacts_with_src_layout',
            project_name,
            metadata_directory=metadata_directory,
            tag=tag,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_shared_data(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        shared_data_path = temp_dir / 'data'
        shared_data_path.ensure_dir_exists()
        (shared_data_path / 'foo.txt').touch()
        nested_data_path = shared_data_path / 'nested'
        nested_data_path.ensure_dir_exists()
        (nested_data_path / 'bar.txt').touch()

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {'targets': {'wheel': {'versions': ['standard'], 'shared-data': {'../data': '/'}}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        shared_data_directory = f'{builder.project_id}.data'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_shared_data',
            project_name,
            metadata_directory=metadata_directory,
            shared_data_directory=shared_data_directory,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_extra_metadata(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        extra_metadata_path = temp_dir / 'data'
        extra_metadata_path.ensure_dir_exists()
        (extra_metadata_path / 'foo.txt').touch()
        nested_data_path = extra_metadata_path / 'nested'
        nested_data_path.ensure_dir_exists()
        (nested_data_path / 'bar.txt').touch()

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {'targets': {'wheel': {'versions': ['standard'], 'extra-metadata': {'../data': '/'}}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_extra_metadata',
            project_name,
            metadata_directory=metadata_directory,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    @pytest.mark.requires_unix
    def test_default_symlink(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.h')

        (temp_dir / 'foo.so').write_bytes(b'data')

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import os
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['pure_python'] = False
                        build_data['infer_tag'] = True

                        pathlib.Path('my_app', 'lib.so').symlink_to(os.path.abspath(os.path.join('..', 'foo.so')))
                        pathlib.Path('my_app', 'lib.h').touch()
                """
            )
        )

        config = {
            'project': {'name': project_name, 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'artifacts': ['my_app/lib.so'],
                        'hooks': {'custom': {'path': DEFAULT_BUILD_SCRIPT}},
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        best_matching_tag = next(sys_tags())
        tag = f'{best_matching_tag.interpreter}-{best_matching_tag.abi}-{best_matching_tag.platform}'
        assert expected_artifact == str(build_path / f'{builder.project_id}-{tag}.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_symlink',
            project_name,
            metadata_directory=metadata_directory,
            tag=tag,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    @fixed_pathlib_resolution
    def test_editable_default(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['src-layout'] = True
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'src/my_app/__about__.py'},
                    'build': {'targets': {'wheel': {'versions': ['editable']}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_editable_pth',
            project_name,
            metadata_directory=metadata_directory,
            package_paths=[str(project_path / 'src')],
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        # Inspect the archive rather than the extracted files because on Windows they lose their metadata
        # https://stackoverflow.com/q/9813243
        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    @fixed_pathlib_resolution
    def test_editable_default_extra_dependencies(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['src-layout'] = True
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['dependencies'].append('binary')
                """
            )
        )

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'src/my_app/__about__.py'},
                    'build': {'targets': {'wheel': {'versions': ['editable'], 'hooks': {'custom': {}}}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_editable_pth_extra_dependencies',
            project_name,
            metadata_directory=metadata_directory,
            package_paths=[str(project_path / 'src')],
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        # Inspect the archive rather than the extracted files because on Windows they lose their metadata
        # https://stackoverflow.com/q/9813243
        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    @fixed_pathlib_resolution
    def test_editable_default_force_include(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['src-layout'] = True
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        # Prefix z just to satisfy our ordering test assertion
                        build_data['force_include_editable']['src/my_app/__about__.py'] = 'zfoo.py'
                """
            )
        )

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'src/my_app/__about__.py'},
                    'build': {'targets': {'wheel': {'versions': ['editable'], 'hooks': {'custom': {}}}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_editable_pth_force_include',
            project_name,
            metadata_directory=metadata_directory,
            package_paths=[str(project_path / 'src')],
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        # Inspect the archive rather than the extracted files because on Windows they lose their metadata
        # https://stackoverflow.com/q/9813243
        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    @fixed_pathlib_resolution
    def test_editable_default_force_include_option(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['src-layout'] = True
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'src/my_app/__about__.py'},
                    'build': {
                        'targets': {
                            'wheel': {
                                'versions': ['editable'],
                                'force-include': {'src/my_app/__about__.py': 'zfoo.py'},
                            }
                        }
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_editable_pth_force_include',
            project_name,
            metadata_directory=metadata_directory,
            package_paths=[str(project_path / 'src')],
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        # Inspect the archive rather than the extracted files because on Windows they lose their metadata
        # https://stackoverflow.com/q/9813243
        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    @fixed_pathlib_resolution
    def test_editable_exact(self, hatch, helpers, temp_dir):
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
                    'build': {'targets': {'wheel': {'versions': ['editable'], 'dev-mode-exact': True}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_editable_exact',
            project_name,
            metadata_directory=metadata_directory,
            package_root=str(project_path / 'my_app' / '__init__.py'),
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        # Inspect the archive rather than the extracted files because on Windows they lose their metadata
        # https://stackoverflow.com/q/9813243
        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    @fixed_pathlib_resolution
    def test_editable_exact_extra_dependencies(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['dependencies'].append('binary')
                """
            )
        )

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {
                            'wheel': {'versions': ['editable'], 'dev-mode-exact': True, 'hooks': {'custom': {}}}
                        }
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_editable_exact_extra_dependencies',
            project_name,
            metadata_directory=metadata_directory,
            package_root=str(project_path / 'my_app' / '__init__.py'),
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        # Inspect the archive rather than the extracted files because on Windows they lose their metadata
        # https://stackoverflow.com/q/9813243
        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    @fixed_pathlib_resolution
    def test_editable_exact_force_include(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        # Prefix z just to satisfy our ordering test assertion
                        build_data['force_include_editable']['my_app/__about__.py'] = 'zfoo.py'
                """
            )
        )

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {
                            'wheel': {'versions': ['editable'], 'dev-mode-exact': True, 'hooks': {'custom': {}}}
                        }
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_editable_exact_force_include',
            project_name,
            metadata_directory=metadata_directory,
            package_root=str(project_path / 'my_app' / '__init__.py'),
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        # Inspect the archive rather than the extracted files because on Windows they lose their metadata
        # https://stackoverflow.com/q/9813243
        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    @fixed_pathlib_resolution
    def test_editable_exact_force_include_option(self, hatch, helpers, temp_dir):
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
                    'build': {
                        'targets': {
                            'wheel': {
                                'versions': ['editable'],
                                'dev-mode-exact': True,
                                'force-include': {'my_app/__about__.py': 'zfoo.py'},
                            }
                        }
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_editable_exact_force_include',
            project_name,
            metadata_directory=metadata_directory,
            package_root=str(project_path / 'my_app' / '__init__.py'),
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        # Inspect the archive rather than the extracted files because on Windows they lose their metadata
        # https://stackoverflow.com/q/9813243
        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    @fixed_pathlib_resolution
    def test_editable_exact_force_include_build_data_precedence(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        build_script = project_path / DEFAULT_BUILD_SCRIPT
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        # Prefix z just to satisfy our ordering test assertion
                        build_data['force_include_editable']['my_app/__about__.py'] = 'zfoo.py'
                """
            )
        )

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {
                            'wheel': {
                                'versions': ['editable'],
                                'dev-mode-exact': True,
                                'force-include': {'my_app/__about__.py': 'zbar.py'},
                                'hooks': {'custom': {}},
                            }
                        }
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_editable_exact_force_include',
            project_name,
            metadata_directory=metadata_directory,
            package_root=str(project_path / 'my_app' / '__init__.py'),
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        # Inspect the archive rather than the extracted files because on Windows they lose their metadata
        # https://stackoverflow.com/q/9813243
        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    @fixed_pathlib_resolution
    def test_editable_pth(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['src-layout'] = True
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'src/my_app/__about__.py'},
                    'build': {'targets': {'wheel': {'versions': ['editable'], 'dev-mode-dirs': ['.']}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_editable_pth',
            project_name,
            metadata_directory=metadata_directory,
            package_paths=[str(project_path)],
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

        # Inspect the archive rather than the extracted files because on Windows they lose their metadata
        # https://stackoverflow.com/q/9813243
        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_info = zip_archive.getinfo(f'{metadata_directory}/WHEEL')
            assert zip_info.date_time == (2020, 2, 2, 0, 0, 0)

    def test_default_namespace_package(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        package_path = project_path / 'my_app'
        namespace_path = project_path / 'namespace'
        namespace_path.mkdir()
        package_path.replace(namespace_path / 'my_app')

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'namespace/my_app/__about__.py'},
                    'build': {'targets': {'wheel': {'versions': ['standard']}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_namespace_package',
            project_name,
            metadata_directory=metadata_directory,
            namespace='namespace',
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_default_entry_points(self, hatch, helpers, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        config = {
            'project': {'name': project_name, 'dynamic': ['version'], 'scripts': {'foo': 'pkg:bar', 'bar': 'pkg:foo'}},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {'targets': {'wheel': {'versions': ['standard']}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(build_path / f'{builder.project_id}-{get_python_versions_tag()}-none-any.whl')

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_entry_points', project_name, metadata_directory=metadata_directory
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_explicit_selection_with_src_layout(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['src-layout'] = True
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'src/my_app/__about__.py'},
                    'build': {
                        'targets': {
                            'wheel': {
                                'versions': ['standard'],
                                'artifacts': ['README.md'],
                                'only-include': ['src/my_app'],
                                'sources': ['src'],
                            }
                        },
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_license_single',
            project_name,
            metadata_directory=metadata_directory,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_single_module(self, hatch, helpers, temp_dir, config_file):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        (project_path / 'my_app').remove()
        (project_path / 'my_app.py').touch()

        config = {'project': {'name': project_name, 'version': '0.0.1'}}
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            artifacts = list(builder.build(str(build_path)))

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_default_single_module',
            project_name,
            metadata_directory=metadata_directory,
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_no_strict_naming(self, hatch, helpers, temp_dir):
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
                    'build': {'targets': {'wheel': {'versions': ['standard'], 'strict-naming': False}}},
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'

        with project_path.as_cwd():
            artifacts = list(builder.build())

        assert len(artifacts) == 1
        expected_artifact = artifacts[0]

        build_artifacts = list(build_path.iterdir())
        assert len(build_artifacts) == 1
        assert expected_artifact == str(build_artifacts[0])
        assert expected_artifact == str(
            build_path / f'{builder.artifact_project_id}-{get_python_versions_tag()}-none-any.whl'
        )

        extraction_directory = temp_dir / '_archive'
        extraction_directory.mkdir()

        with zipfile.ZipFile(str(expected_artifact), 'r') as zip_archive:
            zip_archive.extractall(str(extraction_directory))

        metadata_directory = f'{builder.artifact_project_id}.dist-info'
        expected_files = helpers.get_template_files(
            'wheel.standard_no_strict_naming', project_name, metadata_directory=metadata_directory
        )
        helpers.assert_files(extraction_directory, expected_files, check_contents=True)

    def test_editable_sources_rewrite_error(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['src-layout'] = True
        config_file.save()

        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        config = {
            'project': {'name': project_name, 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'src/my_app/__about__.py'},
                    'build': {
                        'targets': {
                            'wheel': {
                                'versions': ['editable'],
                                'only-include': ['src/my_app'],
                                'sources': {'src/my_app': 'namespace/plugins/my_app'},
                            }
                        },
                    },
                },
            },
        }
        builder = WheelBuilder(str(project_path), config=config)

        build_path = project_path / 'dist'
        build_path.mkdir()

        with project_path.as_cwd():
            with pytest.raises(
                ValueError,
                match=(
                    'Dev mode installations are unsupported when any path rewrite in the `sources` option '
                    'changes a prefix rather than removes it, see: '
                    'https://github.com/pfmoore/editables/issues/20'
                ),
            ):
                list(builder.build(str(build_path)))
