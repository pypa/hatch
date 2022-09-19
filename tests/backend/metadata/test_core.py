import pytest

from hatchling.metadata.core import BuildMetadata, CoreMetadata, HatchMetadata, ProjectMetadata
from hatchling.plugin.manager import PluginManager
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT
from hatchling.version.source.regex import RegexSource


class TestConfig:
    def test_default(self, isolation):
        metadata = ProjectMetadata(str(isolation), None)

        assert metadata.config == metadata.config == {}

    def test_reuse(self, isolation):
        config = {}
        metadata = ProjectMetadata(str(isolation), None, config)

        assert metadata.config is metadata.config is config

    def test_read(self, temp_dir):
        project_file = temp_dir / 'pyproject.toml'
        project_file.write_text('foo = 5')

        with temp_dir.as_cwd():
            metadata = ProjectMetadata(str(temp_dir), None)

            assert metadata.config == metadata.config == {'foo': 5}


class TestInterface:
    def test_types(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        assert metadata.core is metadata._core
        assert isinstance(metadata.core, CoreMetadata)

        assert metadata.hatch is metadata._hatch
        assert isinstance(metadata.hatch, HatchMetadata)

        assert metadata.build is metadata._build
        assert isinstance(metadata.build, BuildMetadata)

    def test_missing_core_metadata(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {})

        with pytest.raises(ValueError, match='Missing `project` metadata table in configuration'):
            _ = metadata.core

    def test_core_metadata_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': 'foo'})

        with pytest.raises(TypeError, match='The `project` configuration must be a table'):
            _ = metadata.core

    def test_tool_metadata_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'tool': 'foo'})

        with pytest.raises(TypeError, match='The `tool` configuration must be a table'):
            _ = metadata.hatch

    def test_hatch_metadata_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'tool': {'hatch': 'foo'}})

        with pytest.raises(TypeError, match='The `tool.hatch` configuration must be a table'):
            _ = metadata.hatch

    def test_build_metadata_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'build-system': 'foo'})

        with pytest.raises(TypeError, match='The `build-system` configuration must be a table'):
            _ = metadata.build


class TestDynamic:
    def test_not_array(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'dynamic': 10}})

        with pytest.raises(TypeError, match='Field `project.dynamic` must be an array'):
            _ = metadata.core.dynamic

    def test_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'dynamic': [10]}})

        with pytest.raises(TypeError, match='Field #1 of field `project.dynamic` must be a string'):
            _ = metadata.core.dynamic

    def test_correct(self, isolation):
        dynamic = ['version']
        metadata = ProjectMetadata(str(isolation), None, {'project': {'dynamic': dynamic}})

        assert metadata.core.dynamic is dynamic
        assert metadata.core.dynamic == ['version']

    def test_cache_not_array(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'dynamic': 10}})

        with pytest.raises(TypeError, match='Field `project.dynamic` must be an array'):
            _ = metadata.dynamic

    def test_cache_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'dynamic': [10]}})

        with pytest.raises(TypeError, match='Field #1 of field `project.dynamic` must be a string'):
            _ = metadata.dynamic

    def test_cache_correct(self, temp_dir, helpers):
        metadata = ProjectMetadata(
            str(temp_dir),
            PluginManager(),
            {
                'project': {'name': 'foo', 'dynamic': ['version', 'description']},
                'tool': {'hatch': {'version': {'path': 'a/b'}, 'metadata': {'hooks': {'custom': {}}}}},
            },
        )

        file_path = temp_dir / 'a' / 'b'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('__version__ = "0.0.1"')

        file_path = temp_dir / DEFAULT_BUILD_SCRIPT
        file_path.write_text(
            helpers.dedent(
                """
                from hatchling.metadata.plugin.interface import MetadataHookInterface

                class CustomHook(MetadataHookInterface):
                    def update(self, metadata):
                        metadata['description'] = metadata['name'] + 'bar'
                """
            )
        )

        # Trigger hooks with `metadata.core` first
        assert metadata.core.dynamic == []
        assert metadata.dynamic == ['version', 'description']


class TestRawName:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'name': 9000, 'dynamic': ['name']}})

        with pytest.raises(
            ValueError, match='Static metadata field `name` cannot be present in field `project.dynamic`'
        ):
            _ = metadata.core.raw_name

    def test_missing(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        with pytest.raises(ValueError, match='Missing required field `project.name`'):
            _ = metadata.core.raw_name

    def test_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'name': 9000}})

        with pytest.raises(TypeError, match='Field `project.name` must be a string'):
            _ = metadata.core.raw_name

    def test_invalid(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'name': 'my app'}})

        with pytest.raises(
            ValueError,
            match=(
                'Required field `project.name` must only contain ASCII letters/digits, underscores, '
                'hyphens, and periods, and must begin and end with ASCII letters/digits.'
            ),
        ):
            _ = metadata.core.raw_name

    def test_correct(self, isolation):
        name = 'My.App'
        metadata = ProjectMetadata(str(isolation), None, {'project': {'name': name}})

        assert metadata.core.raw_name is metadata.core.raw_name is name


class TestName:
    @pytest.mark.parametrize('name', ['My--App', 'My__App', 'My..App'])
    def test_normalization(self, isolation, name):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'name': name}})

        assert metadata.core.name == metadata.core.name == 'my-app'


class TestVersion:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'version': 9000, 'dynamic': ['version']}})

        with pytest.raises(
            ValueError,
            match='Metadata field `version` cannot be both statically defined and listed in field `project.dynamic`',
        ):
            _ = metadata.core.version

    def test_static_missing(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        with pytest.raises(
            ValueError,
            match='Field `project.version` can only be resolved dynamically if `version` is in field `project.dynamic`',
        ):
            _ = metadata.version

    def test_static_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'version': 9000}})

        with pytest.raises(TypeError, match='Field `project.version` must be a string'):
            _ = metadata.version

    def test_static_invalid(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'version': '0..0'}})

        with pytest.raises(
            ValueError,
            match='Invalid version `0..0` from field `project.version`, see https://peps.python.org/pep-0440/',
        ):
            _ = metadata.version

    def test_static_normalization(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'version': '0.1.0.0-rc.1'}})

        assert metadata.version == metadata.version == '0.1.0.0rc1'
        assert metadata.core.version == metadata.core.version == '0.1.0.0-rc.1'

    def test_dynamic_missing(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'dynamic': ['version']}, 'tool': {'hatch': {}}})

        with pytest.raises(ValueError, match='Missing `tool.hatch.version` configuration'):
            _ = metadata.version

    def test_dynamic_not_table(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'dynamic': ['version']}, 'tool': {'hatch': {'version': '1.0'}}}
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.version` must be a table'):
            _ = metadata.version

    def test_dynamic_source_empty(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'dynamic': ['version']}, 'tool': {'hatch': {'version': {'source': ''}}}}
        )

        with pytest.raises(
            ValueError, match='The `source` option under the `tool.hatch.version` table must not be empty if defined'
        ):
            _ = metadata.version.cached

    def test_dynamic_source_not_string(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'dynamic': ['version']}, 'tool': {'hatch': {'version': {'source': 42}}}}
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.version.source` must be a string'):
            _ = metadata.version.cached

    def test_dynamic_unknown_source(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            PluginManager(),
            {'project': {'dynamic': ['version']}, 'tool': {'hatch': {'version': {'source': 'foo'}}}},
        )

        with pytest.raises(ValueError, match='Unknown version source: foo'):
            _ = metadata.version.cached

    def test_dynamic_source_regex(self, temp_dir):
        metadata = ProjectMetadata(
            str(temp_dir),
            PluginManager(),
            {'project': {'dynamic': ['version']}, 'tool': {'hatch': {'version': {'source': 'regex', 'path': 'a/b'}}}},
        )

        file_path = temp_dir / 'a' / 'b'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('__version__ = "0.0.1"')

        assert metadata.hatch.version.source is metadata.hatch.version.source
        assert isinstance(metadata.hatch.version.source, RegexSource)
        assert metadata.hatch.version.cached == metadata.hatch.version.cached == '0.0.1'

    def test_dynamic_source_regex_invalid(self, temp_dir):
        metadata = ProjectMetadata(
            str(temp_dir),
            PluginManager(),
            {'project': {'dynamic': ['version']}, 'tool': {'hatch': {'version': {'source': 'regex', 'path': 'a/b'}}}},
        )

        file_path = temp_dir / 'a' / 'b'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('__version__ = "0..0"')

        with pytest.raises(
            ValueError, match='Invalid version `0..0` from source `regex`, see https://peps.python.org/pep-0440/'
        ):
            _ = metadata.version

    def test_dynamic_error(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            PluginManager(),
            {'project': {'dynamic': ['version']}, 'tool': {'hatch': {'version': {'source': 'regex'}}}},
        )

        with pytest.raises(
            ValueError, match='Error getting the version from source `regex`: option `path` must be specified'
        ):
            _ = metadata.version.cached


class TestDescription:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'description': 9000, 'dynamic': ['description']}})

        with pytest.raises(
            ValueError,
            match=(
                'Metadata field `description` cannot be both statically defined and listed in field `project.dynamic`'
            ),
        ):
            _ = metadata.core.description

    def test_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'description': 9000}})

        with pytest.raises(TypeError, match='Field `project.description` must be a string'):
            _ = metadata.core.description

    def test_default(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        assert metadata.core.description == metadata.core.description == ''

    def test_custom(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'description': 'foo'}})

        assert metadata.core.description == metadata.core.description == 'foo'


class TestReadme:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'readme': 9000, 'dynamic': ['readme']}})

        with pytest.raises(
            ValueError,
            match='Metadata field `readme` cannot be both statically defined and listed in field `project.dynamic`',
        ):
            _ = metadata.core.readme

    @pytest.mark.parametrize('attribute', ['readme', 'readme_content_type'])
    def test_unknown_type(self, isolation, attribute):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'readme': 9000}})

        with pytest.raises(TypeError, match='Field `project.readme` must be a string or a table'):
            _ = getattr(metadata.core, attribute)

    def test_default(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        assert metadata.core.readme == metadata.core.readme == ''
        assert metadata.core.readme_content_type == metadata.core.readme_content_type == 'text/markdown'
        assert metadata.core.readme_path == metadata.core.readme_path == ''

    def test_string_path_unknown_content_type(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'readme': 'foo'}})

        with pytest.raises(
            TypeError, match='Unable to determine the content-type based on the extension of readme file: foo'
        ):
            _ = metadata.core.readme

    def test_string_path_nonexistent(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'readme': 'foo/bar.md'}})

        with pytest.raises(OSError, match='Readme file does not exist: foo/bar\\.md'):
            _ = metadata.core.readme

    @pytest.mark.parametrize(
        'extension, content_type', [('.md', 'text/markdown'), ('.rst', 'text/x-rst'), ('.txt', 'text/plain')]
    )
    def test_string_correct(self, extension, content_type, temp_dir):
        metadata = ProjectMetadata(str(temp_dir), None, {'project': {'readme': f'foo/bar{extension}'}})

        file_path = temp_dir / 'foo' / f'bar{extension}'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('test content')

        assert metadata.core.readme == metadata.core.readme == 'test content'
        assert metadata.core.readme_content_type == metadata.core.readme_content_type == content_type
        assert metadata.core.readme_path == metadata.core.readme_path == f'foo/bar{extension}'

    def test_table_content_type_missing(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'readme': {}}})

        with pytest.raises(ValueError, match='Field `content-type` is required in the `project.readme` table'):
            _ = metadata.core.readme

    def test_table_content_type_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'readme': {'content-type': 5}}})

        with pytest.raises(TypeError, match='Field `content-type` in the `project.readme` table must be a string'):
            _ = metadata.core.readme

    def test_table_content_type_not_unknown(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'readme': {'content-type': 'foo'}}})

        with pytest.raises(
            ValueError,
            match=(
                'Field `content-type` in the `project.readme` table must be one of the following: '
                'text/markdown, text/x-rst, text/plain'
            ),
        ):
            _ = metadata.core.readme

    def test_table_multiple_options(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'readme': {'content-type': 'text/markdown', 'file': '', 'text': ''}}}
        )

        with pytest.raises(ValueError, match='Cannot specify both `file` and `text` in the `project.readme` table'):
            _ = metadata.core.readme

    def test_table_no_option(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'readme': {'content-type': 'text/markdown'}}})

        with pytest.raises(ValueError, match='Must specify either `file` or `text` in the `project.readme` table'):
            _ = metadata.core.readme

    def test_table_file_not_string(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'readme': {'content-type': 'text/markdown', 'file': 4}}}
        )

        with pytest.raises(TypeError, match='Field `file` in the `project.readme` table must be a string'):
            _ = metadata.core.readme

    def test_table_file_nonexistent(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'readme': {'content-type': 'text/markdown', 'file': 'foo/bar.md'}}}
        )

        with pytest.raises(OSError, match='Readme file does not exist: foo/bar\\.md'):
            _ = metadata.core.readme

    def test_table_file_correct(self, temp_dir):
        metadata = ProjectMetadata(
            str(temp_dir), None, {'project': {'readme': {'content-type': 'text/markdown', 'file': 'foo/bar.markdown'}}}
        )

        file_path = temp_dir / 'foo' / 'bar.markdown'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('test content')

        assert metadata.core.readme == metadata.core.readme == 'test content'
        assert metadata.core.readme_content_type == metadata.core.readme_content_type == 'text/markdown'
        assert metadata.core.readme_path == metadata.core.readme_path == 'foo/bar.markdown'

    def test_table_text_not_string(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'readme': {'content-type': 'text/markdown', 'text': 4}}}
        )

        with pytest.raises(TypeError, match='Field `text` in the `project.readme` table must be a string'):
            _ = metadata.core.readme

    def test_table_text_correct(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'readme': {'content-type': 'text/markdown', 'text': 'test content'}}}
        )

        assert metadata.core.readme == metadata.core.readme == 'test content'
        assert metadata.core.readme_content_type == metadata.core.readme_content_type == 'text/markdown'
        assert metadata.core.readme_path == metadata.core.readme_path == ''


class TestRequiresPython:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'requires-python': 9000, 'dynamic': ['requires-python']}}
        )

        with pytest.raises(
            ValueError,
            match=(
                'Metadata field `requires-python` cannot be both statically defined and '
                'listed in field `project.dynamic`'
            ),
        ):
            _ = metadata.core.requires_python

    @pytest.mark.parametrize('attribute', ['requires_python', 'python_constraint'])
    def test_not_string(self, isolation, attribute):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'requires-python': 9000}})

        with pytest.raises(TypeError, match='Field `project.requires-python` must be a string'):
            _ = getattr(metadata.core, attribute)

    def test_invalid(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'requires-python': '^1'}})

        with pytest.raises(ValueError, match='Field `project.requires-python` is invalid: .+'):
            _ = metadata.core.requires_python

    def test_default(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        assert metadata.core.requires_python == metadata.core.requires_python == ''
        for major_version in map(str, range(10)):
            assert metadata.core.python_constraint.contains(major_version)

    def test_custom(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'requires-python': '>2'}})

        assert metadata.core.requires_python == metadata.core.requires_python == '>2'
        assert not metadata.core.python_constraint.contains('2')
        assert metadata.core.python_constraint.contains('3')


class TestLicense:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license': 9000, 'dynamic': ['license']}})

        with pytest.raises(
            ValueError,
            match='Metadata field `license` cannot be both statically defined and listed in field `project.dynamic`',
        ):
            _ = metadata.core.license

    def test_invalid_type(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license': 9000}})

        with pytest.raises(TypeError, match='Field `project.license` must be a string or a table'):
            _ = metadata.core.license

    def test_default(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        assert metadata.core.license == metadata.core.license == ''
        assert metadata.core.license_expression == metadata.core.license_expression == ''

    def test_normalization(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license': 'mit or apache-2.0'}})

        assert metadata.core.license_expression == 'MIT OR Apache-2.0'

    def test_invalid_expression(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license': 'mit or foo'}})

        with pytest.raises(ValueError, match='Error parsing field `project.license` - unknown license: foo'):
            _ = metadata.core.license_expression

    def test_multiple_options(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license': {'file': '', 'text': ''}}})

        with pytest.raises(ValueError, match='Cannot specify both `file` and `text` in the `project.license` table'):
            _ = metadata.core.license

    def test_no_option(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license': {}}})

        with pytest.raises(ValueError, match='Must specify either `file` or `text` in the `project.license` table'):
            _ = metadata.core.license

    def test_file_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license': {'file': 4}}})

        with pytest.raises(TypeError, match='Field `file` in the `project.license` table must be a string'):
            _ = metadata.core.license

    def test_file_nonexistent(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license': {'file': 'foo/bar.md'}}})

        with pytest.raises(OSError, match='License file does not exist: foo/bar\\.md'):
            _ = metadata.core.license

    def test_file_correct(self, temp_dir):
        metadata = ProjectMetadata(str(temp_dir), None, {'project': {'license': {'file': 'foo/bar.md'}}})

        file_path = temp_dir / 'foo' / 'bar.md'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('test content')

        assert metadata.core.license == 'test content'

    def test_text_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license': {'text': 4}}})

        with pytest.raises(TypeError, match='Field `text` in the `project.license` table must be a string'):
            _ = metadata.core.license

    def test_text_correct(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license': {'text': 'test content'}}})

        assert metadata.core.license == 'test content'


class TestLicenseFiles:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'license-files': 9000, 'dynamic': ['license-files']}}
        )

        with pytest.raises(
            ValueError,
            match=(
                'Metadata field `license-files` cannot be both statically defined and '
                'listed in field `project.dynamic`'
            ),
        ):
            _ = metadata.core.license_files

    def test_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license-files': 9000}})

        with pytest.raises(TypeError, match='Field `project.license-files` must be a table'):
            _ = metadata.core.license_files

    def test_multiple_options(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license-files': {'paths': [], 'globs': []}}})

        with pytest.raises(
            ValueError, match='Cannot specify both `paths` and `globs` in the `project.license-files` table'
        ):
            _ = metadata.core.license_files

    def test_no_option(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license-files': {}}})

        with pytest.raises(
            ValueError, match='Must specify either `paths` or `globs` in the `project.license-files` table if defined'
        ):
            _ = metadata.core.license_files

    def test_paths_not_array(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license-files': {'paths': 9000}}})

        with pytest.raises(TypeError, match='Field `paths` in the `project.license-files` table must be an array'):
            _ = metadata.core.license_files

    def test_paths_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license-files': {'paths': [9000]}}})

        with pytest.raises(
            TypeError, match='Entry #1 in field `paths` in the `project.license-files` table must be a string'
        ):
            _ = metadata.core.license_files

    def test_globs_not_array(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license-files': {'globs': 9000}}})

        with pytest.raises(TypeError, match='Field `globs` in the `project.license-files` table must be an array'):
            _ = metadata.core.license_files

    def test_globs_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'license-files': {'globs': [9000]}}})

        with pytest.raises(
            TypeError, match='Entry #1 in field `globs` in the `project.license-files` table must be a string'
        ):
            _ = metadata.core.license_files

    def test_default_globs_no_licenses(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        assert metadata.core.license_files == metadata.core.license_files == []

    def test_default_globs_with_licenses(self, temp_dir):
        metadata = ProjectMetadata(str(temp_dir), None, {'project': {}})

        expected = []
        (temp_dir / 'foo').touch()

        for name in ('LICENSE', 'LICENCE', 'COPYING', 'NOTICE', 'AUTHORS'):
            (temp_dir / name).touch()
            expected.append(name)

            name_with_extension = f'{name}.txt'
            (temp_dir / f'{name}.txt').touch()
            expected.append(name_with_extension)

        assert metadata.core.license_files == sorted(expected)

    def test_globs_with_licenses(self, temp_dir):
        metadata = ProjectMetadata(str(temp_dir), None, {'project': {'license-files': {'globs': ['LICENSES/*']}}})

        licenses_dir = temp_dir / 'LICENSES'
        licenses_dir.mkdir()
        (licenses_dir / 'MIT.txt').touch()
        (licenses_dir / 'Apache-2.0.txt').touch()

        for name in ('LICENSE', 'LICENCE', 'COPYING', 'NOTICE', 'AUTHORS'):
            (temp_dir / name).touch()

        assert metadata.core.license_files == ['LICENSES/Apache-2.0.txt', 'LICENSES/MIT.txt']

    def test_paths_with_licenses(self, temp_dir):
        metadata = ProjectMetadata(
            str(temp_dir),
            None,
            {'project': {'license-files': {'paths': ['LICENSES/Apache-2.0.txt', 'LICENSES/MIT.txt', 'COPYING']}}},
        )

        licenses_dir = temp_dir / 'LICENSES'
        licenses_dir.mkdir()
        (licenses_dir / 'MIT.txt').touch()
        (licenses_dir / 'Apache-2.0.txt').touch()

        for name in ('LICENSE', 'LICENCE', 'COPYING', 'NOTICE', 'AUTHORS'):
            (temp_dir / name).touch()

        assert metadata.core.license_files == ['COPYING', 'LICENSES/Apache-2.0.txt', 'LICENSES/MIT.txt']

    def test_paths_missing_license(self, temp_dir):
        metadata = ProjectMetadata(
            str(temp_dir),
            None,
            {'project': {'license-files': {'paths': ['LICENSES/MIT.txt']}}},
        )

        licenses_dir = temp_dir / 'LICENSES'
        licenses_dir.mkdir()
        (licenses_dir / 'Apache-2.0.txt').touch()

        with pytest.raises(OSError, match='License file does not exist: LICENSES/MIT.txt'):
            _ = metadata.core.license_files


class TestAuthors:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'authors': 9000, 'dynamic': ['authors']}})

        with pytest.raises(
            ValueError,
            match='Metadata field `authors` cannot be both statically defined and listed in field `project.dynamic`',
        ):
            _ = metadata.core.authors

    def test_not_array(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'authors': 'foo'}})

        with pytest.raises(TypeError, match='Field `project.authors` must be an array'):
            _ = metadata.core.authors

    def test_default(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        assert metadata.core.authors == metadata.core.authors == []

    def test_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'authors': ['foo']}})

        with pytest.raises(TypeError, match='Author #1 of field `project.authors` must be an inline table'):
            _ = metadata.core.authors

    def test_no_data(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'authors': [{}]}})

        with pytest.raises(
            ValueError, match='Author #1 of field `project.authors` must specify either `name` or `email`'
        ):
            _ = metadata.core.authors

    def test_name_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'authors': [{'name': 9}]}})

        with pytest.raises(TypeError, match='Name of author #1 of field `project.authors` must be a string'):
            _ = metadata.core.authors

    def test_name_only(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'authors': [{'name': 'foo'}]}})

        assert len(metadata.core.authors) == 1
        assert metadata.core.authors[0] == {'name': 'foo'}
        assert metadata.core.authors_data == metadata.core.authors_data == {'name': ['foo'], 'email': []}

    def test_email_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'authors': [{'email': 9}]}})

        with pytest.raises(TypeError, match='Email of author #1 of field `project.authors` must be a string'):
            _ = metadata.core.authors

    def test_email_only(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'authors': [{'email': 'foo@bar.baz'}]}})

        assert len(metadata.core.authors) == 1
        assert metadata.core.authors[0] == {'email': 'foo@bar.baz'}
        assert metadata.core.authors_data == {'name': [], 'email': ['foo@bar.baz']}

    def test_name_and_email(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'authors': [{'name': 'foo2', 'email': 'foo2@bar.baz'}, {'name': 'foo1', 'email': 'foo1@bar.baz'}]
                }
            },
        )

        assert len(metadata.core.authors) == 2
        assert metadata.core.authors[0] == {'name': 'foo2', 'email': 'foo2@bar.baz'}
        assert metadata.core.authors[1] == {'name': 'foo1', 'email': 'foo1@bar.baz'}
        assert metadata.core.authors_data == {'name': [], 'email': ['foo2 <foo2@bar.baz>', 'foo1 <foo1@bar.baz>']}


class TestMaintainers:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'maintainers': 9000, 'dynamic': ['maintainers']}})

        with pytest.raises(
            ValueError,
            match=(
                'Metadata field `maintainers` cannot be both statically defined and listed in field `project.dynamic`'
            ),
        ):
            _ = metadata.core.maintainers

    def test_not_array(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'maintainers': 'foo'}})

        with pytest.raises(TypeError, match='Field `project.maintainers` must be an array'):
            _ = metadata.core.maintainers

    def test_default(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        assert metadata.core.maintainers == metadata.core.maintainers == []

    def test_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'maintainers': ['foo']}})

        with pytest.raises(TypeError, match='Maintainer #1 of field `project.maintainers` must be an inline table'):
            _ = metadata.core.maintainers

    def test_no_data(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'maintainers': [{}]}})

        with pytest.raises(
            ValueError, match='Maintainer #1 of field `project.maintainers` must specify either `name` or `email`'
        ):
            _ = metadata.core.maintainers

    def test_name_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'maintainers': [{'name': 9}]}})

        with pytest.raises(TypeError, match='Name of maintainer #1 of field `project.maintainers` must be a string'):
            _ = metadata.core.maintainers

    def test_name_only(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'maintainers': [{'name': 'foo'}]}})

        assert len(metadata.core.maintainers) == 1
        assert metadata.core.maintainers[0] == {'name': 'foo'}
        assert metadata.core.maintainers_data == metadata.core.maintainers_data == {'name': ['foo'], 'email': []}

    def test_email_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'maintainers': [{'email': 9}]}})

        with pytest.raises(TypeError, match='Email of maintainer #1 of field `project.maintainers` must be a string'):
            _ = metadata.core.maintainers

    def test_email_only(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'maintainers': [{'email': 'foo@bar.baz'}]}})

        assert len(metadata.core.maintainers) == 1
        assert metadata.core.maintainers[0] == {'email': 'foo@bar.baz'}
        assert metadata.core.maintainers_data == {'name': [], 'email': ['foo@bar.baz']}

    def test_name_and_email(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'maintainers': [
                        {'name': 'foo2', 'email': 'foo2@bar.baz'},
                        {'name': 'foo1', 'email': 'foo1@bar.baz'},
                    ]
                }
            },
        )

        assert len(metadata.core.maintainers) == 2
        assert metadata.core.maintainers[0] == {'name': 'foo2', 'email': 'foo2@bar.baz'}
        assert metadata.core.maintainers[1] == {'name': 'foo1', 'email': 'foo1@bar.baz'}
        assert metadata.core.maintainers_data == {'name': [], 'email': ['foo2 <foo2@bar.baz>', 'foo1 <foo1@bar.baz>']}


class TestKeywords:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'keywords': 9000, 'dynamic': ['keywords']}})

        with pytest.raises(
            ValueError,
            match='Metadata field `keywords` cannot be both statically defined and listed in field `project.dynamic`',
        ):
            _ = metadata.core.keywords

    def test_not_array(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'keywords': 10}})

        with pytest.raises(TypeError, match='Field `project.keywords` must be an array'):
            _ = metadata.core.keywords

    def test_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'keywords': [10]}})

        with pytest.raises(TypeError, match='Keyword #1 of field `project.keywords` must be a string'):
            _ = metadata.core.keywords

    def test_correct(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'keywords': ['foo', 'foo', 'bar']}})

        assert metadata.core.keywords == metadata.core.keywords == ['bar', 'foo']


class TestClassifiers:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'classifiers': 9000, 'dynamic': ['classifiers']}})

        with pytest.raises(
            ValueError,
            match=(
                'Metadata field `classifiers` cannot be both statically defined and listed in field `project.dynamic`'
            ),
        ):
            _ = metadata.core.classifiers

    def test_not_array(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'classifiers': 10}})

        with pytest.raises(TypeError, match='Field `project.classifiers` must be an array'):
            _ = metadata.core.classifiers

    def test_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'classifiers': [10]}})

        with pytest.raises(TypeError, match='Classifier #1 of field `project.classifiers` must be a string'):
            _ = metadata.core.classifiers

    def test_entry_unknown(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'classifiers': ['foo']}})

        with pytest.raises(ValueError, match='Unknown classifier in field `project.classifiers`: foo'):
            _ = metadata.core.classifiers

    def test_correct(self, isolation):
        classifiers = [
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.9',
            'Development Status :: 4 - Beta',
            'Private :: Do Not Upload',
        ]
        metadata = ProjectMetadata(str(isolation), None, {'project': {'classifiers': classifiers}})

        assert (
            metadata.core.classifiers
            == metadata.core.classifiers
            == [
                'Private :: Do Not Upload',
                'Development Status :: 4 - Beta',
                'Programming Language :: Python :: 3.9',
                'Programming Language :: Python :: 3.11',
            ]
        )


class TestURLs:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'urls': 9000, 'dynamic': ['urls']}})

        with pytest.raises(
            ValueError,
            match='Metadata field `urls` cannot be both statically defined and listed in field `project.dynamic`',
        ):
            _ = metadata.core.urls

    def test_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'urls': 10}})

        with pytest.raises(TypeError, match='Field `project.urls` must be a table'):
            _ = metadata.core.urls

    def test_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'urls': {'foo': 7}}})

        with pytest.raises(TypeError, match='URL `foo` of field `project.urls` must be a string'):
            _ = metadata.core.urls

    def test_correct(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'urls': {'foo': 'bar', 'bar': 'baz'}}})

        assert metadata.core.urls == metadata.core.urls == {'bar': 'baz', 'foo': 'bar'}


class TestScripts:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'scripts': 9000, 'dynamic': ['scripts']}})

        with pytest.raises(
            ValueError,
            match='Metadata field `scripts` cannot be both statically defined and listed in field `project.dynamic`',
        ):
            _ = metadata.core.scripts

    def test_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'scripts': 10}})

        with pytest.raises(TypeError, match='Field `project.scripts` must be a table'):
            _ = metadata.core.scripts

    def test_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'scripts': {'foo': 7}}})

        with pytest.raises(TypeError, match='Object reference `foo` of field `project.scripts` must be a string'):
            _ = metadata.core.scripts

    def test_correct(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'scripts': {'foo': 'bar', 'bar': 'baz'}}})

        assert metadata.core.scripts == metadata.core.scripts == {'bar': 'baz', 'foo': 'bar'}


class TestGUIScripts:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'gui-scripts': 9000, 'dynamic': ['gui-scripts']}})

        with pytest.raises(
            ValueError,
            match=(
                'Metadata field `gui-scripts` cannot be both statically defined and listed in field `project.dynamic`'
            ),
        ):
            _ = metadata.core.gui_scripts

    def test_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'gui-scripts': 10}})

        with pytest.raises(TypeError, match='Field `project.gui-scripts` must be a table'):
            _ = metadata.core.gui_scripts

    def test_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'gui-scripts': {'foo': 7}}})

        with pytest.raises(TypeError, match='Object reference `foo` of field `project.gui-scripts` must be a string'):
            _ = metadata.core.gui_scripts

    def test_correct(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'gui-scripts': {'foo': 'bar', 'bar': 'baz'}}})

        assert metadata.core.gui_scripts == metadata.core.gui_scripts == {'bar': 'baz', 'foo': 'bar'}


class TestEntryPoints:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'entry-points': 9000, 'dynamic': ['entry-points']}}
        )

        with pytest.raises(
            ValueError,
            match=(
                'Metadata field `entry-points` cannot be both statically defined and listed in field `project.dynamic`'
            ),
        ):
            _ = metadata.core.entry_points

    def test_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'entry-points': 10}})

        with pytest.raises(TypeError, match='Field `project.entry-points` must be a table'):
            _ = metadata.core.entry_points

    @pytest.mark.parametrize('field', ['scripts', 'gui-scripts'])
    def test_forbidden_fields(self, isolation, field):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'entry-points': {field: 'foo'}}})

        with pytest.raises(
            ValueError,
            match=(
                f'Field `{field}` must be defined as `project.{field}` instead of in the `project.entry-points` table'
            ),
        ):
            _ = metadata.core.entry_points

    def test_data_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'entry-points': {'foo': 7}}})

        with pytest.raises(TypeError, match='Field `project.entry-points.foo` must be a table'):
            _ = metadata.core.entry_points

    def test_data_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'entry-points': {'foo': {'bar': 4}}}})

        with pytest.raises(
            TypeError, match='Object reference `bar` of field `project.entry-points.foo` must be a string'
        ):
            _ = metadata.core.entry_points

    def test_data_empty(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'entry-points': {'foo': {}}}})

        assert metadata.core.entry_points == metadata.core.entry_points == {}

    def test_default(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {}})

        assert metadata.core.entry_points == metadata.core.entry_points == {}

    def test_correct(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'entry-points': {'foo': {'bar': 'baz', 'foo': 'baz'}, 'bar': {'foo': 'baz', 'bar': 'baz'}}}},
        )

        assert (
            metadata.core.entry_points
            == metadata.core.entry_points
            == {'bar': {'bar': 'baz', 'foo': 'baz'}, 'foo': {'bar': 'baz', 'foo': 'baz'}}
        )


class TestDependencies:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'dependencies': 9000, 'dynamic': ['dependencies']}}
        )

        with pytest.raises(
            ValueError,
            match=(
                'Metadata field `dependencies` cannot be both statically defined and listed in field `project.dynamic`'
            ),
        ):
            _ = metadata.core.dependencies

    def test_not_array(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'dependencies': 10}})

        with pytest.raises(TypeError, match='Field `project.dependencies` must be an array'):
            _ = metadata.core.dependencies

    def test_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'dependencies': [10]}})

        with pytest.raises(TypeError, match='Dependency #1 of field `project.dependencies` must be a string'):
            _ = metadata.core.dependencies

    def test_invalid(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'dependencies': ['foo^1']}})

        with pytest.raises(ValueError, match='Dependency #1 of field `project.dependencies` is invalid: .+'):
            _ = metadata.core.dependencies

    def test_direct_reference(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'dependencies': ['proj @ git+https://github.com/org/proj.git@v1']}}
        )

        with pytest.raises(
            ValueError,
            match=(
                'Dependency #1 of field `project.dependencies` cannot be a direct reference unless '
                'field `tool.hatch.metadata.allow-direct-references` is set to `true`'
            ),
        ):
            _ = metadata.core.dependencies

    def test_direct_reference_allowed(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {'dependencies': ['proj @ git+https://github.com/org/proj.git@v1']},
                'tool': {'hatch': {'metadata': {'allow-direct-references': True}}},
            },
        )

        assert metadata.core.dependencies == ['proj@ git+https://github.com/org/proj.git@v1']

    def test_context_formatting(self, isolation, uri_slash_prefix):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {'dependencies': ['proj @ {root:uri}']},
                'tool': {'hatch': {'metadata': {'allow-direct-references': True}}},
            },
        )

        normalized_path = str(isolation).replace('\\', '/')
        assert metadata.core.dependencies == [f'proj@ file:{uri_slash_prefix}{normalized_path}']

    def test_correct(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'dependencies': [
                        'python___dateutil;platform_python_implementation=="CPython"',
                        'bAr.Baz[TLS, Zu.Bat, EdDSA, Zu_Bat]   >=1.2RC5 , <9000B1',
                        'Foo;python_version<"3.8"',
                        'fOO;     python_version<    "3.8"',
                    ],
                },
            },
        )

        assert (
            metadata.core.dependencies
            == metadata.core.dependencies
            == [
                'bar-baz[eddsa,tls,zu-bat]<9000b1,>=1.2rc5',
                "foo; python_version < '3.8'",
                "python-dateutil; platform_python_implementation == 'CPython'",
            ]
        )
        assert metadata.core.dependencies_complex is metadata.core.dependencies_complex


class TestOptionalDependencies:
    def test_dynamic(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'optional-dependencies': 9000, 'dynamic': ['optional-dependencies']}}
        )

        with pytest.raises(
            ValueError,
            match=(
                'Metadata field `optional-dependencies` cannot be both statically defined and '
                'listed in field `project.dynamic`'
            ),
        ):
            _ = metadata.core.optional_dependencies

    def test_not_table(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'optional-dependencies': 10}})

        with pytest.raises(TypeError, match='Field `project.optional-dependencies` must be a table'):
            _ = metadata.core.optional_dependencies

    def test_invalid_name(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'optional-dependencies': {'foo/bar': []}}})

        with pytest.raises(
            ValueError,
            match=(
                'Optional dependency group `foo/bar` of field `project.optional-dependencies` must only contain '
                'ASCII letters/digits, underscores, hyphens, and periods, and must begin and end with '
                'ASCII letters/digits.'
            ),
        ):
            _ = metadata.core.optional_dependencies

    def test_definitions_not_array(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'optional-dependencies': {'foo': 5}}})

        with pytest.raises(
            TypeError, match='Dependencies for option `foo` of field `project.optional-dependencies` must be an array'
        ):
            _ = metadata.core.optional_dependencies

    def test_entry_not_string(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'optional-dependencies': {'foo': [5]}}})

        with pytest.raises(
            TypeError, match='Dependency #1 of option `foo` of field `project.optional-dependencies` must be a string'
        ):
            _ = metadata.core.optional_dependencies

    def test_invalid(self, isolation):
        metadata = ProjectMetadata(str(isolation), None, {'project': {'optional-dependencies': {'foo': ['bar^1']}}})

        with pytest.raises(
            ValueError, match='Dependency #1 of option `foo` of field `project.optional-dependencies` is invalid: .+'
        ):
            _ = metadata.core.optional_dependencies

    def test_conflict(self, isolation):
        metadata = ProjectMetadata(
            str(isolation), None, {'project': {'optional-dependencies': {'foo_bar': [], 'foo.bar': []}}}
        )

        with pytest.raises(
            ValueError,
            match=(
                'Optional dependency groups `foo_bar` and `foo.bar` of field `project.optional-dependencies` both '
                'evaluate to `foo-bar`.'
            ),
        ):
            _ = metadata.core.optional_dependencies

    def test_allow_ambiguity(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {'optional-dependencies': {'foo_bar': [], 'foo.bar': []}},
                'tool': {'hatch': {'metadata': {'allow-ambiguous-features': True}}},
            },
        )

        assert metadata.core.optional_dependencies == {'foo_bar': [], 'foo.bar': []}

    def test_direct_reference(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {'project': {'optional-dependencies': {'foo': ['proj @ git+https://github.com/org/proj.git@v1']}}},
        )

        with pytest.raises(
            ValueError,
            match=(
                'Dependency #1 of option `foo` of field `project.optional-dependencies` cannot be a direct reference '
                'unless field `tool.hatch.metadata.allow-direct-references` is set to `true`'
            ),
        ):
            _ = metadata.core.optional_dependencies

    def test_context_formatting(self, isolation, uri_slash_prefix):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {'optional-dependencies': {'foo': ['proj @ {root:uri}']}},
                'tool': {'hatch': {'metadata': {'allow-direct-references': True}}},
            },
        )

        normalized_path = str(isolation).replace('\\', '/')
        assert metadata.core.optional_dependencies == {'foo': [f'proj@ file:{uri_slash_prefix}{normalized_path}']}

    def test_direct_reference_allowed(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {'optional-dependencies': {'foo': ['proj @ git+https://github.com/org/proj.git@v1']}},
                'tool': {'hatch': {'metadata': {'allow-direct-references': True}}},
            },
        )

        assert metadata.core.optional_dependencies == {'foo': ['proj@ git+https://github.com/org/proj.git@v1']}

    def test_correct(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            None,
            {
                'project': {
                    'optional-dependencies': {
                        'foo': [
                            'python___dateutil;platform_python_implementation=="CPython"',
                            'bAr.Baz[TLS, Zu.Bat, EdDSA, Zu_Bat]   >=1.2RC5 , <9000B1',
                            'Foo;python_version<"3.8"',
                            'fOO;     python_version<    "3.8"',
                        ],
                        'bar': ['foo', 'bar', 'Baz'],
                    },
                },
            },
        )

        assert (
            metadata.core.optional_dependencies
            == metadata.core.optional_dependencies
            == {
                'bar': ['bar', 'baz', 'foo'],
                'foo': [
                    'bar-baz[eddsa,tls,zu-bat]<9000b1,>=1.2rc5',
                    "foo; python_version < '3.8'",
                    "python-dateutil; platform_python_implementation == 'CPython'",
                ],
            }
        )


class TestHook:
    def test_unknown(self, isolation):
        metadata = ProjectMetadata(
            str(isolation),
            PluginManager(),
            {'project': {'name': 'foo'}, 'tool': {'hatch': {'metadata': {'hooks': {'foo': {}}}}}},
        )

        with pytest.raises(ValueError, match='Unknown metadata hook: foo'):
            _ = metadata.core

    def test_custom(self, temp_dir, helpers):
        classifiers = [
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.9',
            'Framework :: Foo',
            'Development Status :: 4 - Beta',
            'Private :: Do Not Upload',
        ]
        metadata = ProjectMetadata(
            str(temp_dir),
            PluginManager(),
            {
                'project': {'name': 'foo', 'classifiers': classifiers, 'dynamic': ['version', 'description']},
                'tool': {'hatch': {'version': {'path': 'a/b'}, 'metadata': {'hooks': {'custom': {}}}}},
            },
        )

        file_path = temp_dir / 'a' / 'b'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('__version__ = "0.0.1"')

        file_path = temp_dir / DEFAULT_BUILD_SCRIPT
        file_path.write_text(
            helpers.dedent(
                """
                from hatchling.metadata.plugin.interface import MetadataHookInterface

                class CustomHook(MetadataHookInterface):
                    def update(self, metadata):
                        metadata['description'] = metadata['name'] + 'bar'
                        metadata['version'] = metadata['version'] + 'rc0'

                    def get_known_classifiers(self):
                        return ['Framework :: Foo']
                """
            )
        )

        assert 'custom' in metadata.hatch.metadata.hooks
        assert metadata.core.name == 'foo'
        assert metadata.core.description == 'foobar'
        assert metadata.core.version == '0.0.1rc0'
        assert metadata.core.classifiers == [
            'Private :: Do Not Upload',
            'Development Status :: 4 - Beta',
            'Framework :: Foo',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.11',
        ]

    def test_custom_missing_dynamic(self, temp_dir, helpers):
        metadata = ProjectMetadata(
            str(temp_dir),
            PluginManager(),
            {
                'project': {'name': 'foo', 'dynamic': ['version']},
                'tool': {'hatch': {'version': {'path': 'a/b'}, 'metadata': {'hooks': {'custom': {}}}}},
            },
        )

        file_path = temp_dir / 'a' / 'b'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('__version__ = "0.0.1"')

        file_path = temp_dir / DEFAULT_BUILD_SCRIPT
        file_path.write_text(
            helpers.dedent(
                """
                from hatchling.metadata.plugin.interface import MetadataHookInterface

                class CustomHook(MetadataHookInterface):
                    def update(self, metadata):
                        metadata['description'] = metadata['name'] + 'bar'
                """
            )
        )

        with pytest.raises(
            ValueError,
            match='The field `description` was set dynamically and therefore must be listed in `project.dynamic`',
        ):
            _ = metadata.core


class TestHatchPersonalProjectConfigFile:
    def test_correct(self, isolation, temp_dir, helpers):
        metadata = ProjectMetadata(
            str(temp_dir),
            PluginManager(),
            {
                'project': {'name': 'foo', 'dynamic': ['version']},
                'tool': {'hatch': {'build': {'reproducible': False}}},
            },
        )

        file_path = temp_dir / 'a' / 'b'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('__version__ = "0.0.1"')

        (temp_dir / 'pyproject.toml').touch()
        file_path = temp_dir / 'hatch.toml'
        file_path.write_text(
            helpers.dedent(
                """
                [version]
                path = 'a/b'
                """
            )
        )

        assert metadata.version == '0.0.1'
        assert metadata.hatch.build_config['reproducible'] is False

    def test_precedence(self, isolation, temp_dir, helpers):
        metadata = ProjectMetadata(
            str(temp_dir),
            PluginManager(),
            {
                'project': {'name': 'foo', 'dynamic': ['version']},
                'tool': {'hatch': {'version': {'path': 'a/b'}, 'build': {'reproducible': False}}},
            },
        )

        file_path = temp_dir / 'a' / 'b'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('__version__ = "0.0.1"')

        file_path = temp_dir / 'c' / 'd'
        file_path.ensure_parent_dir_exists()
        file_path.write_text('__version__ = "0.0.2"')

        (temp_dir / 'pyproject.toml').touch()
        file_path = temp_dir / 'hatch.toml'
        file_path.write_text(
            helpers.dedent(
                """
                [version]
                path = 'c/d'
                """
            )
        )

        assert metadata.version == '0.0.2'
        assert metadata.hatch.build_config['reproducible'] is False
