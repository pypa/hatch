import re
from os.path import join as pjoin

import pathspec
import pytest

from hatchling.builders.plugin.interface import BuilderInterface


class TestDirectory:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.directory == builder.config.directory == str(isolation / 'dist')

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'directory': 'bar'}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.directory == str(isolation / 'bar')

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'directory': 9000}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.directory` must be a string'):
            _ = builder.config.directory

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'directory': 'bar'}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.directory == str(isolation / 'bar')

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'directory': 9000}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.directory` must be a string'):
            _ = builder.config.directory

    def test_target_overrides_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'directory': 'bar', 'targets': {'foo': {'directory': 'baz'}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.directory == str(isolation / 'baz')

    def test_absolute_path(self, isolation):
        absolute_path = str(isolation)
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'directory': absolute_path}}}}}}
        builder = BuilderInterface(absolute_path, config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.directory == absolute_path


class TestIgnoreVCS:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.ignore_vcs is builder.config.ignore_vcs is False

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'ignore-vcs': True}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.ignore_vcs is True

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'ignore-vcs': 9000}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.ignore-vcs` must be a boolean'):
            _ = builder.config.ignore_vcs

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'ignore-vcs': True}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.ignore_vcs is True

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'ignore-vcs': 9000}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.ignore-vcs` must be a boolean'):
            _ = builder.config.ignore_vcs

    def test_target_overrides_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'ignore-vcs': True, 'targets': {'foo': {'ignore-vcs': False}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.ignore_vcs is False


class TestReproducible:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.reproducible is builder.config.reproducible is True

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'reproducible': False}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.reproducible is False

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'reproducible': 9000}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.reproducible` must be a boolean'):
            _ = builder.config.reproducible

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'reproducible': False}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.reproducible is False

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'reproducible': 9000}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.reproducible` must be a boolean'):
            _ = builder.config.reproducible

    def test_target_overrides_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'reproducible': False, 'targets': {'foo': {'reproducible': True}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.reproducible is True


class TestDevModeDirs:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.dev_mode_dirs == builder.config.dev_mode_dirs == []

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-dirs': ''}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.dev-mode-dirs` must be an array of strings'):
            _ = builder.config.dev_mode_dirs

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-dirs': ['foo', 'bar/baz']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.config.dev_mode_dirs == ['foo', 'bar/baz']

    def test_global_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-dirs': [0]}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Directory #1 in field `tool.hatch.build.dev-mode-dirs` must be a string'):
            _ = builder.config.dev_mode_dirs

    def test_global_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-dirs': ['']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Directory #1 in field `tool.hatch.build.dev-mode-dirs` cannot be an empty string'
        ):
            _ = builder.config.dev_mode_dirs

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dev-mode-dirs': ['foo', 'bar/baz']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dev_mode_dirs == ['foo', 'bar/baz']

    def test_target_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dev-mode-dirs': [0]}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Directory #1 in field `tool.hatch.build.targets.foo.dev-mode-dirs` must be a string'
        ):
            _ = builder.config.dev_mode_dirs

    def test_target_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dev-mode-dirs': ['']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError,
            match='Directory #1 in field `tool.hatch.build.targets.foo.dev-mode-dirs` cannot be an empty string',
        ):
            _ = builder.config.dev_mode_dirs

    def test_target_overrides_global(self, isolation):
        config = {
            'tool': {'hatch': {'build': {'dev-mode-dirs': ['foo'], 'targets': {'foo': {'dev-mode-dirs': ['bar']}}}}}
        }
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dev_mode_dirs == ['bar']


class TestPackages:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.package_sources == builder.config.package_sources == []
        assert builder.config.packages == builder.config.packages == []
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('src', 'foo', 'bar.py')

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': ''}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.packages` must be an array of strings'):
            _ = builder.config.packages

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': ['src/foo']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert len(builder.config.packages) == 1
        assert len(builder.config.package_sources) == 1
        assert builder.config.packages[0] == pjoin('src', 'foo')
        assert builder.config.package_sources[0] == pjoin('src', '')
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('foo', 'bar.py')

    def test_global_package_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': [0]}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Package #1 in field `tool.hatch.build.packages` must be a string'):
            _ = builder.config.packages

    def test_global_package_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': ['']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Package #1 in field `tool.hatch.build.packages` cannot be an empty string'
        ):
            _ = builder.config.packages

    def test_global_duplicate_package_name(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': ['src/foo', 'pkg/foo']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(
            ValueError,
            match=re.escape(
                f'Package `foo` of field `tool.hatch.build.packages` is already defined '
                f'by path `{pjoin("pkg", "foo")}`'
            ),
        ):
            _ = builder.config.packages

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'packages': ['src/foo']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert len(builder.config.packages) == 1
        assert len(builder.config.package_sources) == 1
        assert builder.config.packages[0] == pjoin('src', 'foo')
        assert builder.config.package_sources[0] == pjoin('src', '')
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('foo', 'bar.py')

    def test_target_package_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'packages': [0]}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Package #1 in field `tool.hatch.build.targets.foo.packages` must be a string'
        ):
            _ = builder.config.packages

    def test_target_package_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'packages': ['']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError, match='Package #1 in field `tool.hatch.build.targets.foo.packages` cannot be an empty string'
        ):
            _ = builder.config.packages

    def test_target_duplicate_package_name(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'packages': ['src/foo', 'pkg/foo']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError,
            match=re.escape(
                f'Package `foo` of field `tool.hatch.build.targets.foo.packages` is already defined '
                f'by path `{pjoin("pkg", "foo")}`'
            ),
        ):
            _ = builder.config.packages

    def test_target_overrides_global(self, isolation):
        config = {
            'tool': {'hatch': {'build': {'packages': ['src/foo'], 'targets': {'foo': {'packages': ['pkg/foo']}}}}}
        }
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert len(builder.config.packages) == 1
        assert len(builder.config.package_sources) == 1
        assert builder.config.packages[0] == pjoin('pkg', 'foo')
        assert builder.config.package_sources[0] == pjoin('pkg', '')
        assert builder.config.get_distribution_path(pjoin('pkg', 'foo', 'bar.py')) == pjoin('foo', 'bar.py')
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('src', 'foo', 'bar.py')

    def test_no_source(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': ['foo']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert len(builder.config.packages) == 1
        assert len(builder.config.package_sources) == 0
        assert builder.config.packages[0] == pjoin('foo')
        assert builder.config.get_distribution_path(pjoin('foo', 'bar.py')) == pjoin('foo', 'bar.py')


class TestVersions:
    def test_default_known(self, isolation):
        builder = BuilderInterface(str(isolation))
        builder.PLUGIN_NAME = 'foo'
        builder.get_version_api = lambda: {'2': str, '1': str}

        assert builder.config.versions == builder.config.versions == ['2', '1']

    def test_default_override(self, isolation):
        builder = BuilderInterface(str(isolation))
        builder.PLUGIN_NAME = 'foo'
        builder.get_default_versions = lambda: ['old', 'new', 'new']

        assert builder.config.versions == builder.config.versions == ['old', 'new']

    def test_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ''}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Field `tool.hatch.build.targets.foo.versions` must be an array of strings'
        ):
            _ = builder.config.versions

    def test_correct(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ['3.14', '1', '3.14']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'
        builder.get_version_api = lambda: {'3.14': str, '42': str, '1': str}

        assert builder.config.versions == builder.config.versions == ['3.14', '1']

    def test_empty_default(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': []}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'
        builder.get_default_versions = lambda: ['old', 'new']

        assert builder.config.versions == builder.config.versions == ['old', 'new']

    def test_version_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': [1]}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Version #1 in field `tool.hatch.build.targets.foo.versions` must be a string'
        ):
            _ = builder.config.versions

    def test_version_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ['']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError, match='Version #1 in field `tool.hatch.build.targets.foo.versions` cannot be an empty string'
        ):
            _ = builder.config.versions

    def test_unknown_version(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ['9000', '1', '42']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'
        builder.get_version_api = lambda: {'1': str}

        with pytest.raises(
            ValueError, match='Unknown versions in field `tool.hatch.build.targets.foo.versions`: 42, 9000'
        ):
            _ = builder.config.versions


class TestHookConfig:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.hook_config == builder.config.hook_config == {}

    def test_target_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'hooks': 'bar'}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.hooks` must be a table'):
            _ = builder.config.hook_config

    def test_target_hook_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'hooks': {'bar': 'baz'}}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.hooks.bar` must be a table'):
            _ = builder.config.hook_config

    def test_global_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': 'foo'}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.hooks` must be a table'):
            _ = builder.config.hook_config

    def test_global_hook_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': 'bar'}}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.hooks.foo` must be a table'):
            _ = builder.config.hook_config

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'bar': 'baz'}}}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.config.hook_config['foo']['bar'] == 'baz'

    def test_target_overrides_global(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {'hooks': {'foo': {'bar': 'baz'}}, 'targets': {'foo': {'hooks': {'foo': {'baz': 'bar'}}}}}
                }
            },
        }
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.hook_config['foo']['baz'] == 'bar'


class TestDependencies:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.dependencies == builder.config.dependencies == []

    def test_target_not_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dependencies': 9000}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.dependencies` must be an array'):
            _ = builder.config.dependencies

    def test_target_dependency_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dependencies': [9000]}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Dependency #1 of field `tool.hatch.build.targets.foo.dependencies` must be a string'
        ):
            _ = builder.config.dependencies

    def test_global_not_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'dependencies': 9000}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.dependencies` must be an array'):
            _ = builder.config.dependencies

    def test_global_dependency_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'dependencies': [9000]}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Dependency #1 of field `tool.hatch.build.dependencies` must be a string'):
            _ = builder.config.dependencies

    def test_hook_not_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'dependencies': 9000}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Option `dependencies` of build hook `foo` must be an array'):
            _ = builder.config.dependencies

    def test_hook_dependency_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'dependencies': [9000]}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Dependency #1 of option `dependencies` of build hook `foo` must be a string'
        ):
            _ = builder.config.dependencies

    def test_correct(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'dependencies': ['bar'],
                        'hooks': {'foobar': {'dependencies': ['test1']}},
                        'targets': {'foo': {'dependencies': ['baz'], 'hooks': {'foobar': {'dependencies': ['test2']}}}},
                    }
                }
            }
        }
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dependencies == ['baz', 'bar', 'test2']


class TestPatternDefaults:
    def test_include(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.default_include_patterns() == []

    def test_exclude(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.default_exclude_patterns() == []

    def test_global_exclude(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.default_global_exclude_patterns() == ['.git']


class TestPatternInclude:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.include_spec is None

    def test_global_becomes_spec(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ['foo']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert isinstance(builder.config.include_spec, pathspec.PathSpec)

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ''}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.include` must be an array of strings'):
            _ = builder.config.include_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_global(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'include': ['foo', 'bar/baz']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.config.include_spec.match_file(f'foo{separator}file.py')
        assert builder.config.include_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.include_spec.match_file(f'bar{separator}file.py')

    def test_global_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': [0]}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Pattern #1 in field `tool.hatch.build.include` must be a string'):
            _ = builder.config.include_spec

    def test_global_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ['']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Pattern #1 in field `tool.hatch.build.include` cannot be an empty string'
        ):
            _ = builder.config.include_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_global_packages_included(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'packages': ['bar'], 'include': ['foo']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.config.include_spec.match_file(f'foo{separator}file.py')
        assert builder.config.include_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.include_spec.match_file(f'baz{separator}bar{separator}file.py')

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'include': ['foo', 'bar/baz']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.include_spec.match_file(f'foo{separator}file.py')
        assert builder.config.include_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.include_spec.match_file(f'bar{separator}file.py')

    def test_target_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'include': [0]}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Pattern #1 in field `tool.hatch.build.targets.foo.include` must be a string'
        ):
            _ = builder.config.include_spec

    def test_target_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'include': ['']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError, match='Pattern #1 in field `tool.hatch.build.targets.foo.include` cannot be an empty string'
        ):
            _ = builder.config.include_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target_overrides_global(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'include': ['foo'], 'targets': {'foo': {'include': ['bar']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert not builder.config.include_spec.match_file(f'foo{separator}file.py')
        assert builder.config.include_spec.match_file(f'bar{separator}file.py')

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target_packages_included(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'packages': ['bar'], 'include': ['foo']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.include_spec.match_file(f'foo{separator}file.py')
        assert builder.config.include_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.include_spec.match_file(f'baz{separator}bar{separator}file.py')


class TestPatternExclude:
    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_default(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        builder = BuilderInterface(str(isolation))

        assert isinstance(builder.config.exclude_spec, pathspec.PathSpec)
        assert builder.config.exclude_spec.match_file(f'.git{separator}file.py')

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'exclude': ''}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.exclude` must be an array of strings'):
            _ = builder.config.exclude_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_global(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'exclude': ['foo', 'bar/baz']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.config.exclude_spec.match_file(f'foo{separator}file.py')
        assert builder.config.exclude_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.exclude_spec.match_file(f'bar{separator}file.py')

    def test_global_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'exclude': [0]}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Pattern #1 in field `tool.hatch.build.exclude` must be a string'):
            _ = builder.config.exclude_spec

    def test_global_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'exclude': ['']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Pattern #1 in field `tool.hatch.build.exclude` cannot be an empty string'
        ):
            _ = builder.config.exclude_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'exclude': ['foo', 'bar/baz']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.exclude_spec.match_file(f'foo{separator}file.py')
        assert builder.config.exclude_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.exclude_spec.match_file(f'bar{separator}file.py')

    def test_target_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'exclude': [0]}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Pattern #1 in field `tool.hatch.build.targets.foo.exclude` must be a string'
        ):
            _ = builder.config.exclude_spec

    def test_target_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'exclude': ['']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError, match='Pattern #1 in field `tool.hatch.build.targets.foo.exclude` cannot be an empty string'
        ):
            _ = builder.config.exclude_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target_overrides_global(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'exclude': ['foo'], 'targets': {'foo': {'exclude': ['bar']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert not builder.config.exclude_spec.match_file(f'foo{separator}file.py')
        assert builder.config.exclude_spec.match_file(f'bar{separator}file.py')

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_vcs(self, temp_dir, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        with temp_dir.as_cwd():
            config = {'tool': {'hatch': {'build': {'exclude': ['foo']}}}}
            builder = BuilderInterface(str(temp_dir), config=config)

            vcs_ignore_file = temp_dir / '.gitignore'
            vcs_ignore_file.write_text('/bar\n*.pyc')

            assert builder.config.exclude_spec.match_file(f'foo{separator}file.py')
            assert builder.config.exclude_spec.match_file(f'bar{separator}file.py')
            assert builder.config.exclude_spec.match_file(f'baz{separator}bar{separator}file.pyc')
            assert not builder.config.exclude_spec.match_file(f'baz{separator}bar{separator}file.py')

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_ignore_vcs(self, temp_dir, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        with temp_dir.as_cwd():
            config = {'tool': {'hatch': {'build': {'ignore-vcs': True, 'exclude': ['foo']}}}}
            builder = BuilderInterface(str(temp_dir), config=config)

            vcs_ignore_file = temp_dir / '.gitignore'
            vcs_ignore_file.write_text('/bar\n*.pyc')

            assert builder.config.exclude_spec.match_file(f'foo{separator}file.py')
            assert not builder.config.exclude_spec.match_file(f'bar{separator}file.py')

    def test_override_default_global_exclude_patterns(self, isolation):
        builder = BuilderInterface(str(isolation))
        builder.config.default_global_exclude_patterns = lambda: []

        assert builder.config.exclude_spec is None
        assert not builder.config.path_is_excluded('.git/file')


class TestPatternArtifacts:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.artifact_spec is None

    def test_global_becomes_spec(self, isolation):
        config = {'tool': {'hatch': {'build': {'artifacts': ['foo']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert isinstance(builder.config.artifact_spec, pathspec.PathSpec)

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'artifacts': ''}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.artifacts` must be an array of strings'):
            _ = builder.config.artifact_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_global(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'artifacts': ['foo', 'bar/baz']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.config.artifact_spec.match_file(f'foo{separator}file.py')
        assert builder.config.artifact_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.artifact_spec.match_file(f'bar{separator}file.py')

    def test_global_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'artifacts': [0]}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Pattern #1 in field `tool.hatch.build.artifacts` must be a string'):
            _ = builder.config.artifact_spec

    def test_global_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'artifacts': ['']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Pattern #1 in field `tool.hatch.build.artifacts` cannot be an empty string'
        ):
            _ = builder.config.artifact_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'artifacts': ['foo', 'bar/baz']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.artifact_spec.match_file(f'foo{separator}file.py')
        assert builder.config.artifact_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.artifact_spec.match_file(f'bar{separator}file.py')

    def test_target_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'artifacts': [0]}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Pattern #1 in field `tool.hatch.build.targets.foo.artifacts` must be a string'
        ):
            _ = builder.config.artifact_spec

    def test_target_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'artifacts': ['']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError, match='Pattern #1 in field `tool.hatch.build.targets.foo.artifacts` cannot be an empty string'
        ):
            _ = builder.config.artifact_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target_overrides_global(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'artifacts': ['foo'], 'targets': {'foo': {'artifacts': ['bar']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert not builder.config.artifact_spec.match_file(f'foo{separator}file.py')
        assert builder.config.artifact_spec.match_file(f'bar{separator}file.py')


class TestPatternMatching:
    def test_include_explicit(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ['foo']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.config.include_path('foo/file.py')
        assert not builder.config.include_path('bar/file.py')

    def test_no_include_greedy(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.config.include_path('foo/file.py')
        assert builder.config.include_path('bar/file.py')

    def test_exclude_precedence(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ['foo'], 'exclude': ['foo']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert not builder.config.include_path('foo/file.py')
        assert not builder.config.include_path('bar/file.py')

    def test_artifact_super_precedence(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ['foo'], 'exclude': ['foo'], 'artifacts': ['foo']}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.config.include_path('foo/file.py')
        assert not builder.config.include_path('bar/file.py')
