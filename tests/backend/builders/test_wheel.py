import zipfile

import pytest
from packaging.tags import sys_tags

from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.builders.utils import get_known_python_major_versions
from hatchling.builders.wheel import WheelBuilder
from hatchling.metadata.utils import DEFAULT_METADATA_VERSION, get_core_metadata_constructors


def get_python_versions_tag():
    return '.'.join(f'py{major_version}' for major_version in get_known_python_major_versions())


def test_class():
    assert issubclass(WheelBuilder, BuilderInterface)


def test_default_versions(isolation):
    builder = WheelBuilder(str(isolation))

    assert builder.get_default_versions() == ['standard']


class TestPatternDefaults:
    def test_include(self, isolation):
        builder = WheelBuilder(str(isolation))

        assert builder.config.default_include_patterns() == []

    def test_exclude(self, isolation):
        builder = WheelBuilder(str(isolation))

        assert builder.config.default_exclude_patterns() == []

    def test_global_exclude(self, isolation):
        builder = WheelBuilder(str(isolation))

        assert builder.config.default_global_exclude_patterns() == ['.git']


class TestZipSafe:
    def test_default(self, isolation):
        builder = WheelBuilder(str(isolation))

        assert builder.zip_safe is builder.zip_safe is True

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'zip-safe': False}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        assert builder.zip_safe is builder.zip_safe is False


class TestCoreMetadataConstructor:
    def test_default(self, isolation):
        builder = WheelBuilder(str(isolation))

        assert builder.core_metadata_constructor is builder.core_metadata_constructor
        assert builder.core_metadata_constructor is get_core_metadata_constructors()[DEFAULT_METADATA_VERSION]

    def test_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'wheel': {'core-metadata-version': 42}}}}}}
        builder = WheelBuilder(str(isolation), config=config)

        with pytest.raises(
            TypeError, match='Field `tool.hatch.build.targets.wheel.core-metadata-version` must be a string'
        ):
            _ = builder.core_metadata_constructor

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
            _ = builder.core_metadata_constructor


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
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        config = {
            'project': {'name': 'my__app', 'dynamic': ['version']},
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
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version']},
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
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'dynamic': ['version']},
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
        project_name = 'My App'
        config_file.model.template.licenses.default = ['MIT', 'Apache-2.0']
        config_file.save()

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        # Ensure that we trigger the non-file case for code coverage
        (project_path / 'LICENSES' / 'test').mkdir()

        config = {
            'project': {'name': 'my__app', 'dynamic': ['version'], 'license-files': {'globs': ['LICENSES/*']}},
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
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        config = {
            'project': {'name': 'my__app', 'dynamic': ['version']},
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

    def test_default_python_constraint(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'
        config = {
            'project': {'name': 'my__app', 'requires-python': '>3', 'dynamic': ['version']},
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
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        build_script = project_path / 'build.py'
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
            'project': {'name': 'my__app', 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'hooks': {'custom': {'path': 'build.py'}},
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
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        build_script = project_path / 'build.py'
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
            'project': {'name': 'my__app', 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'hooks': {'custom': {'path': 'build.py'}},
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
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.h')

        build_script = project_path / 'build.py'
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['zip_safe'] = False
                        build_data['infer_tag'] = True

                        pathlib.Path('my_app', 'lib.so').touch()
                        pathlib.Path('my_app', 'lib.h').touch()
                """
            )
        )

        config = {
            'project': {'name': 'my__app', 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'artifacts': ['my_app/lib.so'],
                        'hooks': {'custom': {'path': 'build.py'}},
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

    def test_default_build_script_dynamic_artifacts(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.h')

        build_script = project_path / 'build.py'
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['zip_safe'] = False
                        build_data['infer_tag'] = True
                        build_data['artifacts'] = ['my_app/lib.so']

                        pathlib.Path('my_app', 'lib.so').touch()
                        pathlib.Path('my_app', 'lib.h').touch()
                """
            )
        )

        config = {
            'project': {'name': 'my__app', 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard']}},
                        'hooks': {'custom': {'path': 'build.py'}},
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

    def test_default_build_script_dynamic_artifacts_with_src_layout(self, hatch, helpers, temp_dir, config_file):
        config_file.model.template.plugins['default']['src-layout'] = True
        config_file.save()

        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        vcs_ignore_file = project_path / '.gitignore'
        vcs_ignore_file.write_text('*.pyc\n*.so\n*.pyd\n*.h')

        build_script = project_path / 'build.py'
        build_script.write_text(
            helpers.dedent(
                """
                import pathlib

                from hatchling.builders.hooks.plugin.interface import BuildHookInterface

                class CustomHook(BuildHookInterface):
                    def initialize(self, version, build_data):
                        build_data['zip_safe'] = False
                        build_data['infer_tag'] = True
                        build_data['artifacts'] = ['src/my_app/lib.so', 'src/lib.pyd']

                        pathlib.Path('src', 'my_app', 'lib.so').touch()
                        pathlib.Path('src', 'lib.h').touch()
                        pathlib.Path('src', 'lib.pyd').touch()
                """
            )
        )

        config = {
            'project': {'name': 'my__app', 'requires-python': '>3', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'src/my_app/__about__.py'},
                    'build': {
                        'targets': {'wheel': {'versions': ['standard'], 'packages': ['src/my_app']}},
                        'hooks': {'custom': {'path': 'build.py'}},
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

    def test_editable_standard(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        config = {
            'project': {'name': 'my__app', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
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
            'wheel.standard_editable_standard',
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

    def test_editable_pth(self, hatch, helpers, temp_dir):
        project_name = 'My App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 0, result.output

        project_path = temp_dir / 'my-app'

        config = {
            'project': {'name': 'my__app', 'dynamic': ['version']},
            'tool': {
                'hatch': {
                    'version': {'path': 'my_app/__about__.py'},
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
