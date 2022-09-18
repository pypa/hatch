import os
import re
from os.path import join as pjoin

import pathspec
import pytest

from hatch.utils.structures import EnvVars
from hatchling.builders.constants import BuildEnvVars
from hatchling.builders.plugin.interface import BuilderInterface


class Builder(BuilderInterface):
    def get_version_api(self):
        return {}


class TestDirectory:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.directory == builder.config.directory == str(isolation / 'dist')

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'directory': 'bar'}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.directory == str(isolation / 'bar')

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'directory': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.directory` must be a string'):
            _ = builder.config.directory

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'directory': 'bar'}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.directory == str(isolation / 'bar')

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'directory': 9000}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.directory` must be a string'):
            _ = builder.config.directory

    def test_target_overrides_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'directory': 'bar', 'targets': {'foo': {'directory': 'baz'}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.directory == str(isolation / 'baz')

    def test_absolute_path(self, isolation):
        absolute_path = str(isolation)
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'directory': absolute_path}}}}}}
        builder = Builder(absolute_path, config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.directory == absolute_path


class TestSkipExcludedDirs:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.skip_excluded_dirs is builder.config.skip_excluded_dirs is False

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'skip-excluded-dirs': True}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.skip_excluded_dirs is True

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'skip-excluded-dirs': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Field `tool.hatch.build.targets.foo.skip-excluded-dirs` must be a boolean'
        ):
            _ = builder.config.skip_excluded_dirs

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'skip-excluded-dirs': True}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.skip_excluded_dirs is True

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'skip-excluded-dirs': 9000}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.skip-excluded-dirs` must be a boolean'):
            _ = builder.config.skip_excluded_dirs

    def test_target_overrides_global(self, isolation):
        config = {
            'tool': {
                'hatch': {'build': {'skip-excluded-dirs': True, 'targets': {'foo': {'skip-excluded-dirs': False}}}}
            }
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.skip_excluded_dirs is False


class TestIgnoreVCS:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.ignore_vcs is builder.config.ignore_vcs is False

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'ignore-vcs': True}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.ignore_vcs is True

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'ignore-vcs': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.ignore-vcs` must be a boolean'):
            _ = builder.config.ignore_vcs

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'ignore-vcs': True}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.ignore_vcs is True

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'ignore-vcs': 9000}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.ignore-vcs` must be a boolean'):
            _ = builder.config.ignore_vcs

    def test_target_overrides_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'ignore-vcs': True, 'targets': {'foo': {'ignore-vcs': False}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.ignore_vcs is False


class TestRequireRuntimeDependencies:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.require_runtime_dependencies is builder.config.require_runtime_dependencies is False

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'require-runtime-dependencies': True}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.require_runtime_dependencies is True

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'require-runtime-dependencies': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError,
            match='Field `tool.hatch.build.targets.foo.require-runtime-dependencies` must be a boolean',
        ):
            _ = builder.config.require_runtime_dependencies

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'require-runtime-dependencies': True}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.require_runtime_dependencies is True

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'require-runtime-dependencies': 9000}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.require-runtime-dependencies` must be a boolean'):
            _ = builder.config.require_runtime_dependencies

    def test_target_overrides_global(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'require-runtime-dependencies': True,
                        'targets': {'foo': {'require-runtime-dependencies': False}},
                    }
                }
            }
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.require_runtime_dependencies is False


class TestRequireRuntimeFeatures:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.require_runtime_features == builder.config.require_runtime_features == []

    def test_target(self, isolation):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'optional-dependencies': {'foo': [], 'bar': []}},
            'tool': {'hatch': {'build': {'targets': {'foo': {'require-runtime-features': ['foo', 'bar']}}}}},
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.require_runtime_features == ['foo', 'bar']

    def test_target_not_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'require-runtime-features': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Field `tool.hatch.build.targets.foo.require-runtime-features` must be an array'
        ):
            _ = builder.config.require_runtime_features

    def test_target_feature_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'require-runtime-features': [9000]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError,
            match='Feature #1 of field `tool.hatch.build.targets.foo.require-runtime-features` must be a string',
        ):
            _ = builder.config.require_runtime_features

    def test_target_feature_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'require-runtime-features': ['']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError,
            match=(
                'Feature #1 of field `tool.hatch.build.targets.foo.require-runtime-features` cannot be an empty string'
            ),
        ):
            _ = builder.config.require_runtime_features

    def test_target_feature_unknown(self, isolation):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'build': {'targets': {'foo': {'require-runtime-features': ['foo_bar']}}}}},
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError,
            match=(
                'Feature `foo-bar` of field `tool.hatch.build.targets.foo.require-runtime-features` is not defined in '
                'field `project.optional-dependencies`'
            ),
        ):
            _ = builder.config.require_runtime_features

    def test_global(self, isolation):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'optional-dependencies': {'foo': [], 'bar': []}},
            'tool': {'hatch': {'build': {'require-runtime-features': ['foo', 'bar']}}},
        }
        builder = Builder(str(isolation), config=config)

        assert builder.config.require_runtime_features == ['foo', 'bar']

    def test_global_not_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'require-runtime-features': 9000}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.require-runtime-features` must be an array'):
            _ = builder.config.require_runtime_features

    def test_global_feature_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'require-runtime-features': [9000]}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            TypeError, match='Feature #1 of field `tool.hatch.build.require-runtime-features` must be a string'
        ):
            _ = builder.config.require_runtime_features

    def test_global_feature_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'require-runtime-features': ['']}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError,
            match='Feature #1 of field `tool.hatch.build.require-runtime-features` cannot be an empty string',
        ):
            _ = builder.config.require_runtime_features

    def test_global_feature_unknown(self, isolation):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'build': {'require-runtime-features': ['foo_bar']}}},
        }
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError,
            match=(
                'Feature `foo-bar` of field `tool.hatch.build.require-runtime-features` is not defined in '
                'field `project.optional-dependencies`'
            ),
        ):
            _ = builder.config.require_runtime_features

    def test_target_overrides_global(self, isolation):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'optional-dependencies': {'foo_bar': [], 'bar_baz': []}},
            'tool': {
                'hatch': {
                    'build': {
                        'require-runtime-features': ['bar_baz'],
                        'targets': {'foo': {'require-runtime-features': ['foo_bar']}},
                    }
                }
            },
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.require_runtime_features == ['foo-bar']


class TestOnlyPackages:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.only_packages is builder.config.only_packages is False

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'only-packages': True}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.only_packages is True

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'only-packages': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.only-packages` must be a boolean'):
            _ = builder.config.only_packages

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'only-packages': True}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.only_packages is True

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'only-packages': 9000}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.only-packages` must be a boolean'):
            _ = builder.config.only_packages

    def test_target_overrides_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'only-packages': True, 'targets': {'foo': {'only-packages': False}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.only_packages is False


class TestReproducible:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.reproducible is builder.config.reproducible is True

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'reproducible': False}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.reproducible is False

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'reproducible': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.reproducible` must be a boolean'):
            _ = builder.config.reproducible

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'reproducible': False}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.reproducible is False

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'reproducible': 9000}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.reproducible` must be a boolean'):
            _ = builder.config.reproducible

    def test_target_overrides_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'reproducible': False, 'targets': {'foo': {'reproducible': True}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.reproducible is True


class TestDevModeDirs:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.dev_mode_dirs == builder.config.dev_mode_dirs == []

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-dirs': ''}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.dev-mode-dirs` must be an array of strings'):
            _ = builder.config.dev_mode_dirs

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-dirs': ['foo', 'bar/baz']}}}}
        builder = Builder(str(isolation), config=config)

        assert builder.config.dev_mode_dirs == ['foo', 'bar/baz']

    def test_global_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-dirs': [0]}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Directory #1 in field `tool.hatch.build.dev-mode-dirs` must be a string'):
            _ = builder.config.dev_mode_dirs

    def test_global_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-dirs': ['']}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Directory #1 in field `tool.hatch.build.dev-mode-dirs` cannot be an empty string'
        ):
            _ = builder.config.dev_mode_dirs

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dev-mode-dirs': ['foo', 'bar/baz']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dev_mode_dirs == ['foo', 'bar/baz']

    def test_target_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dev-mode-dirs': [0]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Directory #1 in field `tool.hatch.build.targets.foo.dev-mode-dirs` must be a string'
        ):
            _ = builder.config.dev_mode_dirs

    def test_target_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dev-mode-dirs': ['']}}}}}}
        builder = Builder(str(isolation), config=config)
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
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dev_mode_dirs == ['bar']


class TestDevModeExact:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.dev_mode_exact is builder.config.dev_mode_exact is False

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dev-mode-exact': True}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dev_mode_exact is True

    def test_target_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dev-mode-exact': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.dev-mode-exact` must be a boolean'):
            _ = builder.config.dev_mode_exact

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-exact': True}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dev_mode_exact is True

    def test_global_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-exact': 9000}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.dev-mode-exact` must be a boolean'):
            _ = builder.config.dev_mode_exact

    def test_target_overrides_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'dev-mode-exact': True, 'targets': {'foo': {'dev-mode-exact': False}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dev_mode_exact is False


class TestPackages:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.packages == builder.config.packages == []

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': ''}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.packages` must be an array of strings'):
            _ = builder.config.packages

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': ['src/foo']}}}}
        builder = Builder(str(isolation), config=config)

        assert len(builder.config.packages) == 1
        assert builder.config.packages[0] == pjoin('src', 'foo')

    def test_global_package_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': [0]}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Package #1 in field `tool.hatch.build.packages` must be a string'):
            _ = builder.config.packages

    def test_global_package_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': ['']}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Package #1 in field `tool.hatch.build.packages` cannot be an empty string'
        ):
            _ = builder.config.packages

    def test_target(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'packages': ['src/foo']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert len(builder.config.packages) == 1
        assert builder.config.packages[0] == pjoin('src', 'foo')

    def test_target_package_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'packages': [0]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Package #1 in field `tool.hatch.build.targets.foo.packages` must be a string'
        ):
            _ = builder.config.packages

    def test_target_package_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'packages': ['']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError, match='Package #1 in field `tool.hatch.build.targets.foo.packages` cannot be an empty string'
        ):
            _ = builder.config.packages

    def test_target_overrides_global(self, isolation):
        config = {
            'tool': {'hatch': {'build': {'packages': ['src/foo'], 'targets': {'foo': {'packages': ['pkg/foo']}}}}}
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert len(builder.config.packages) == 1
        assert builder.config.packages[0] == pjoin('pkg', 'foo')

    def test_no_source(self, isolation):
        config = {'tool': {'hatch': {'build': {'packages': ['foo']}}}}
        builder = Builder(str(isolation), config=config)

        assert len(builder.config.packages) == 1
        assert builder.config.packages[0] == pjoin('foo')


class TestSources:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.sources == builder.config.sources == {}
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('src', 'foo', 'bar.py')

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': ''}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.sources` must be a mapping or array of strings'):
            _ = builder.config.sources

    def test_global_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': ['src']}}}}
        builder = Builder(str(isolation), config=config)

        assert len(builder.config.sources) == 1
        assert builder.config.sources[pjoin('src', '')] == ''
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('foo', 'bar.py')

    def test_global_array_source_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': [0]}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Source #1 in field `tool.hatch.build.sources` must be a string'):
            _ = builder.config.sources

    def test_global_array_source_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': ['']}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(ValueError, match='Source #1 in field `tool.hatch.build.sources` cannot be an empty string'):
            _ = builder.config.sources

    def test_global_mapping(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': {'src/foo': 'renamed'}}}}}
        builder = Builder(str(isolation), config=config)

        assert len(builder.config.sources) == 1
        assert builder.config.sources[pjoin('src', 'foo', '')] == pjoin('renamed', '')
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('renamed', 'bar.py')

    def test_global_mapping_source_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': {'': 'renamed'}}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(ValueError, match='Source #1 in field `tool.hatch.build.sources` cannot be an empty string'):
            _ = builder.config.sources

    def test_global_mapping_path_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': {'src/foo': ''}}}}}
        builder = Builder(str(isolation), config=config)

        assert len(builder.config.sources) == 1
        assert builder.config.sources[pjoin('src', 'foo', '')] == ''
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == 'bar.py'

    def test_global_mapping_replacement_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': {'src/foo': 0}}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            TypeError, match='Path for source `src/foo` in field `tool.hatch.build.sources` must be a string'
        ):
            _ = builder.config.sources

    def test_target_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'sources': ''}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Field `tool.hatch.build.targets.foo.sources` must be a mapping or array of strings'
        ):
            _ = builder.config.sources

    def test_target_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'sources': ['src']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert len(builder.config.sources) == 1
        assert builder.config.sources[pjoin('src', '')] == ''
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('foo', 'bar.py')

    def test_target_array_source_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'sources': [0]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Source #1 in field `tool.hatch.build.targets.foo.sources` must be a string'
        ):
            _ = builder.config.sources

    def test_target_array_source_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'sources': ['']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError, match='Source #1 in field `tool.hatch.build.targets.foo.sources` cannot be an empty string'
        ):
            _ = builder.config.sources

    def test_target_mapping(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'sources': {'src/foo': 'renamed'}}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert len(builder.config.sources) == 1
        assert builder.config.sources[pjoin('src', 'foo', '')] == pjoin('renamed', '')
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('renamed', 'bar.py')

    def test_target_mapping_source_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'sources': {'': 'renamed'}}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError, match='Source #1 in field `tool.hatch.build.targets.foo.sources` cannot be an empty string'
        ):
            _ = builder.config.sources

    def test_target_mapping_path_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'sources': {'src/foo': ''}}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert len(builder.config.sources) == 1
        assert builder.config.sources[pjoin('src', 'foo', '')] == ''
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == 'bar.py'

    def test_target_mapping_replacement_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'sources': {'src/foo': 0}}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError,
            match='Path for source `src/foo` in field `tool.hatch.build.targets.foo.sources` must be a string',
        ):
            _ = builder.config.sources

    def test_target_overrides_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': ['src'], 'targets': {'foo': {'sources': ['pkg']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert len(builder.config.sources) == 1
        assert builder.config.sources[pjoin('pkg', '')] == ''
        assert builder.config.get_distribution_path(pjoin('pkg', 'foo', 'bar.py')) == pjoin('foo', 'bar.py')
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('src', 'foo', 'bar.py')

    def test_no_source(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': ['bar']}}}}
        builder = Builder(str(isolation), config=config)

        assert len(builder.config.sources) == 1
        assert builder.config.sources[pjoin('bar', '')] == ''
        assert builder.config.get_distribution_path(pjoin('foo', 'bar.py')) == pjoin('foo', 'bar.py')

    def test_compatible_with_packages(self, isolation):
        config = {'tool': {'hatch': {'build': {'sources': {'src/foo': 'renamed'}, 'packages': ['src/foo']}}}}
        builder = Builder(str(isolation), config=config)

        assert len(builder.config.sources) == 1
        assert builder.config.sources[pjoin('src', 'foo', '')] == pjoin('renamed', '')
        assert builder.config.get_distribution_path(pjoin('src', 'foo', 'bar.py')) == pjoin('renamed', 'bar.py')


class TestForceInclude:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.force_include == builder.config.force_include == {}

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'force-include': ''}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.force-include` must be a mapping'):
            _ = builder.config.force_include

    def test_global_absolute(self, isolation):
        config = {'tool': {'hatch': {'build': {'force-include': {str(isolation / 'source'): '/target/'}}}}}
        builder = Builder(str(isolation), config=config)

        assert builder.config.force_include == {str(isolation / 'source'): 'target'}

    def test_global_relative(self, isolation):
        config = {'tool': {'hatch': {'build': {'force-include': {'../source': '/target/'}}}}}
        builder = Builder(str(isolation / 'foo'), config=config)

        assert builder.config.force_include == {str(isolation / 'source'): 'target'}

    def test_global_source_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'force-include': {'': '/target/'}}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Source #1 in field `tool.hatch.build.force-include` cannot be an empty string'
        ):
            _ = builder.config.force_include

    def test_global_relative_path_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'force-include': {'source': 0}}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            TypeError, match='Path for source `source` in field `tool.hatch.build.force-include` must be a string'
        ):
            _ = builder.config.force_include

    def test_global_relative_path_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'force-include': {'source': ''}}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError,
            match='Path for source `source` in field `tool.hatch.build.force-include` cannot be an empty string',
        ):
            _ = builder.config.force_include

    def test_target_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'force-include': ''}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.force-include` must be a mapping'):
            _ = builder.config.force_include

    def test_target_absolute(self, isolation):
        config = {
            'tool': {
                'hatch': {'build': {'targets': {'foo': {'force-include': {str(isolation / 'source'): '/target/'}}}}}
            }
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.force_include == {str(isolation / 'source'): 'target'}

    def test_target_relative(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'force-include': {'../source': '/target/'}}}}}}}
        builder = Builder(str(isolation / 'foo'), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.force_include == {str(isolation / 'source'): 'target'}

    def test_target_source_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'force-include': {'': '/target/'}}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError,
            match='Source #1 in field `tool.hatch.build.targets.foo.force-include` cannot be an empty string',
        ):
            _ = builder.config.force_include

    def test_target_relative_path_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'force-include': {'source': 0}}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError,
            match='Path for source `source` in field `tool.hatch.build.targets.foo.force-include` must be a string',
        ):
            _ = builder.config.force_include

    def test_target_relative_path_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'force-include': {'source': ''}}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError,
            match=(
                'Path for source `source` in field `tool.hatch.build.targets.foo.force-include` '
                'cannot be an empty string'
            ),
        ):
            _ = builder.config.force_include

    def test_order(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'force-include': {
                            '../very-nested': 'target1/embedded',
                            '../source1': '/target2/',
                            '../source2': '/target1/',
                        }
                    }
                }
            }
        }
        builder = Builder(str(isolation / 'foo'), config=config)

        assert builder.config.force_include == {
            str(isolation / 'source2'): 'target1',
            str(isolation / 'very-nested'): f'target1{os.sep}embedded',
            str(isolation / 'source1'): 'target2',
        }


class TestIncludeOnly:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.only_include == builder.config.only_include == {}

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'only-include': 9000}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.only-include` must be an array'):
            _ = builder.config.only_include

    def test_global_path_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'only-include': [9000]}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Path #1 in field `tool.hatch.build.only-include` must be a string'):
            _ = builder.config.only_include

    @pytest.mark.parametrize('path', ['/', '~/foo', '../foo'])
    def test_global_not_relative(self, isolation, path):
        config = {'tool': {'hatch': {'build': {'only-include': [path]}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError, match=f'Path #1 in field `tool.hatch.build.only-include` must be relative: {path}'
        ):
            _ = builder.config.only_include

    def test_global_duplicate(self, isolation):
        config = {'tool': {'hatch': {'build': {'only-include': ['/foo//bar', 'foo//bar/']}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError, match=re.escape(f'Duplicate path in field `tool.hatch.build.only-include`: foo{os.sep}bar')
        ):
            _ = builder.config.only_include

    def test_global_correct(self, isolation):
        config = {'tool': {'hatch': {'build': {'only-include': ['/foo//bar/']}}}}
        builder = Builder(str(isolation), config=config)

        assert builder.config.only_include == {f'{isolation}{os.sep}foo{os.sep}bar': f'foo{os.sep}bar'}

    def test_target_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'only-include': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.only-include` must be an array'):
            _ = builder.config.only_include

    def test_target_path_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'only-include': [9000]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Path #1 in field `tool.hatch.build.targets.foo.only-include` must be a string'
        ):
            _ = builder.config.only_include

    @pytest.mark.parametrize('path', ['/', '~/foo', '../foo'])
    def test_target_not_relative(self, isolation, path):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'only-include': [path]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError, match=f'Path #1 in field `tool.hatch.build.targets.foo.only-include` must be relative: {path}'
        ):
            _ = builder.config.only_include

    def test_target_duplicate(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'only-include': ['/foo//bar', 'foo//bar/']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError,
            match=re.escape(f'Duplicate path in field `tool.hatch.build.targets.foo.only-include`: foo{os.sep}bar'),
        ):
            _ = builder.config.only_include

    def test_target_correct(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'only-include': ['/foo//bar/']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.only_include == {f'{isolation}{os.sep}foo{os.sep}bar': f'foo{os.sep}bar'}


class TestVersions:
    def test_default_known(self, isolation):
        builder = Builder(str(isolation))
        builder.PLUGIN_NAME = 'foo'
        builder.get_version_api = lambda: {'2': str, '1': str}

        assert builder.config.versions == builder.config.versions == ['2', '1']

    def test_default_override(self, isolation):
        builder = Builder(str(isolation))
        builder.PLUGIN_NAME = 'foo'
        builder.get_default_versions = lambda: ['old', 'new', 'new']

        assert builder.config.versions == builder.config.versions == ['old', 'new']

    def test_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ''}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Field `tool.hatch.build.targets.foo.versions` must be an array of strings'
        ):
            _ = builder.config.versions

    def test_correct(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ['3.14', '1', '3.14']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'
        builder.get_version_api = lambda: {'3.14': str, '42': str, '1': str}

        assert builder.config.versions == builder.config.versions == ['3.14', '1']

    def test_empty_default(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': []}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'
        builder.get_default_versions = lambda: ['old', 'new']

        assert builder.config.versions == builder.config.versions == ['old', 'new']

    def test_version_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': [1]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Version #1 in field `tool.hatch.build.targets.foo.versions` must be a string'
        ):
            _ = builder.config.versions

    def test_version_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ['']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError, match='Version #1 in field `tool.hatch.build.targets.foo.versions` cannot be an empty string'
        ):
            _ = builder.config.versions

    def test_unknown_version(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ['9000', '1', '42']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'
        builder.get_version_api = lambda: {'1': str}

        with pytest.raises(
            ValueError, match='Unknown versions in field `tool.hatch.build.targets.foo.versions`: 42, 9000'
        ):
            _ = builder.config.versions


class TestHookConfig:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.hook_config == builder.config.hook_config == {}

    def test_target_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'hooks': 'bar'}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.hooks` must be a table'):
            _ = builder.config.hook_config

    def test_target_hook_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'hooks': {'bar': 'baz'}}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.hooks.bar` must be a table'):
            _ = builder.config.hook_config

    def test_global_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': 'foo'}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.hooks` must be a table'):
            _ = builder.config.hook_config

    def test_global_hook_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': 'bar'}}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.hooks.foo` must be a table'):
            _ = builder.config.hook_config

    def test_global(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'bar': 'baz'}}}}}}
        builder = Builder(str(isolation), config=config)

        assert builder.config.hook_config['foo']['bar'] == 'baz'

    def test_order(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {'hooks': {'foo': {'bar': 'baz'}}, 'targets': {'foo': {'hooks': {'baz': {'foo': 'bar'}}}}}
                }
            },
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.hook_config == {'foo': {'bar': 'baz'}, 'baz': {'foo': 'bar'}}

    def test_target_overrides_global(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {'hooks': {'foo': {'bar': 'baz'}}, 'targets': {'foo': {'hooks': {'foo': {'baz': 'bar'}}}}}
                }
            },
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.hook_config['foo']['baz'] == 'bar'

    def test_env_var_no_hooks(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'bar': 'baz'}}}}}}
        builder = Builder(str(isolation), config=config)

        with EnvVars({BuildEnvVars.NO_HOOKS: 'true'}):
            assert builder.config.hook_config == {}

    def test_enable_by_default(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {'bar': 'baz', 'enable-by-default': False},
                            'bar': {'foo': 'baz', 'enable-by-default': False},
                            'baz': {'foo': 'bar'},
                        }
                    }
                }
            }
        }
        builder = Builder(str(isolation), config=config)

        assert builder.config.hook_config == {'baz': {'foo': 'bar'}}

    def test_env_var_all_override_enable_by_default(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {'bar': 'baz', 'enable-by-default': False},
                            'bar': {'foo': 'baz', 'enable-by-default': False},
                            'baz': {'foo': 'bar'},
                        }
                    }
                }
            }
        }
        builder = Builder(str(isolation), config=config)

        with EnvVars({BuildEnvVars.HOOKS_ENABLE: 'true'}):
            assert builder.config.hook_config == {
                'foo': {'bar': 'baz', 'enable-by-default': False},
                'bar': {'foo': 'baz', 'enable-by-default': False},
                'baz': {'foo': 'bar'},
            }

    def test_env_var_specific_override_enable_by_default(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {'bar': 'baz', 'enable-by-default': False},
                            'bar': {'foo': 'baz', 'enable-by-default': False},
                            'baz': {'foo': 'bar'},
                        }
                    }
                }
            }
        }
        builder = Builder(str(isolation), config=config)

        with EnvVars({f'{BuildEnvVars.HOOK_ENABLE_PREFIX}FOO': 'true'}):
            assert builder.config.hook_config == {
                'foo': {'bar': 'baz', 'enable-by-default': False},
                'baz': {'foo': 'bar'},
            }


class TestDependencies:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.dependencies == builder.config.dependencies == []

    def test_target_not_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dependencies': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo.dependencies` must be an array'):
            _ = builder.config.dependencies

    def test_target_dependency_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'dependencies': [9000]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Dependency #1 of field `tool.hatch.build.targets.foo.dependencies` must be a string'
        ):
            _ = builder.config.dependencies

    def test_global_not_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'dependencies': 9000}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.dependencies` must be an array'):
            _ = builder.config.dependencies

    def test_global_dependency_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'dependencies': [9000]}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Dependency #1 of field `tool.hatch.build.dependencies` must be a string'):
            _ = builder.config.dependencies

    def test_hook_require_runtime_dependencies_not_boolean(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'require-runtime-dependencies': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Option `require-runtime-dependencies` of build hook `foo` must be a boolean'
        ):
            _ = builder.config.dependencies

    def test_hook_require_runtime_features_not_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'require-runtime-features': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Option `require-runtime-features` of build hook `foo` must be an array'):
            _ = builder.config.dependencies

    def test_hook_require_runtime_features_feature_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'require-runtime-features': [9000]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Feature #1 of option `require-runtime-features` of build hook `foo` must be a string'
        ):
            _ = builder.config.dependencies

    def test_hook_require_runtime_features_feature_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'require-runtime-features': ['']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError,
            match='Feature #1 of option `require-runtime-features` of build hook `foo` cannot be an empty string',
        ):
            _ = builder.config.dependencies

    def test_hook_require_runtime_features_feature_unknown(self, isolation):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'build': {'hooks': {'foo': {'require-runtime-features': ['foo_bar']}}}}},
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            ValueError,
            match=(
                'Feature `foo-bar` of option `require-runtime-features` of build hook `foo` is not defined in '
                'field `project.optional-dependencies`'
            ),
        ):
            _ = builder.config.dependencies

    def test_hook_dependencies_not_array(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'dependencies': 9000}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Option `dependencies` of build hook `foo` must be an array'):
            _ = builder.config.dependencies

    def test_hook_dependency_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'dependencies': [9000]}}}}}}
        builder = Builder(str(isolation), config=config)
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
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dependencies == ['baz', 'bar', 'test2']

    def test_require_runtime_dependencies(self, isolation):
        config = {
            'project': {'name': 'my-app', 'version': '0.0.1', 'dependencies': ['foo']},
            'tool': {
                'hatch': {
                    'build': {
                        'require-runtime-dependencies': True,
                        'dependencies': ['bar'],
                        'hooks': {'foobar': {'dependencies': ['test1']}},
                        'targets': {'foo': {'dependencies': ['baz'], 'hooks': {'foobar': {'dependencies': ['test2']}}}},
                    }
                }
            },
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dependencies == ['baz', 'bar', 'test2', 'foo']

    def test_require_runtime_features(self, isolation):
        config = {
            'project': {'name': 'my-app', 'version': '0.0.1', 'optional-dependencies': {'bar_baz': ['foo']}},
            'tool': {
                'hatch': {
                    'build': {
                        'require-runtime-features': ['bar-baz'],
                        'dependencies': ['bar'],
                        'hooks': {'foobar': {'dependencies': ['test1']}},
                        'targets': {'foo': {'dependencies': ['baz'], 'hooks': {'foobar': {'dependencies': ['test2']}}}},
                    }
                }
            },
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dependencies == ['baz', 'bar', 'test2', 'foo']

    def test_env_var_no_hooks(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {'dependencies': ['foo']},
                            'bar': {'dependencies': ['bar']},
                            'baz': {'dependencies': ['baz']},
                        },
                    }
                }
            }
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with EnvVars({BuildEnvVars.NO_HOOKS: 'true'}):
            assert builder.config.dependencies == []

    def test_hooks_enable_by_default(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {'dependencies': ['foo'], 'enable-by-default': False},
                            'bar': {'dependencies': ['bar'], 'enable-by-default': False},
                            'baz': {'dependencies': ['baz']},
                        },
                    }
                }
            }
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dependencies == ['baz']

    def test_hooks_env_var_all_override_enable_by_default(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {'dependencies': ['foo'], 'enable-by-default': False},
                            'bar': {'dependencies': ['bar'], 'enable-by-default': False},
                            'baz': {'dependencies': ['baz']},
                        },
                    }
                }
            }
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with EnvVars({BuildEnvVars.HOOKS_ENABLE: 'true'}):
            assert builder.config.dependencies == ['foo', 'bar', 'baz']

    def test_hooks_env_var_specific_override_enable_by_default(self, isolation):
        config = {
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {'dependencies': ['foo'], 'enable-by-default': False},
                            'bar': {'dependencies': ['bar'], 'enable-by-default': False},
                            'baz': {'dependencies': ['baz']},
                        },
                    }
                }
            }
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with EnvVars({f'{BuildEnvVars.HOOK_ENABLE_PREFIX}FOO': 'true'}):
            assert builder.config.dependencies == ['foo', 'baz']

    def test_hooks_require_runtime_dependencies(self, isolation):
        config = {
            'project': {'name': 'my-app', 'version': '0.0.1', 'dependencies': ['baz']},
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {'dependencies': ['foo'], 'enable-by-default': False},
                            'bar': {'dependencies': ['bar'], 'require-runtime-dependencies': True},
                        },
                    }
                }
            },
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dependencies == ['bar', 'baz']

    def test_hooks_require_runtime_dependencies_disabled(self, isolation):
        config = {
            'project': {'name': 'my-app', 'version': '0.0.1', 'dependencies': ['baz']},
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {
                                'dependencies': ['foo'],
                                'enable-by-default': False,
                                'require-runtime-dependencies': True,
                            },
                            'bar': {'dependencies': ['bar']},
                        },
                    }
                }
            },
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dependencies == ['bar']

    def test_hooks_require_runtime_features(self, isolation):
        config = {
            'project': {'name': 'my-app', 'version': '0.0.1', 'optional-dependencies': {'foo_bar': ['baz']}},
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {'dependencies': ['foo'], 'enable-by-default': False},
                            'bar': {'dependencies': ['bar'], 'require-runtime-features': ['foo-bar']},
                        },
                    }
                }
            },
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dependencies == ['bar', 'baz']

    def test_hooks_require_runtime_features_disabled(self, isolation):
        config = {
            'project': {'name': 'my-app', 'version': '0.0.1', 'optional-dependencies': {'foo_bar': ['baz']}},
            'tool': {
                'hatch': {
                    'build': {
                        'hooks': {
                            'foo': {
                                'dependencies': ['foo'],
                                'enable-by-default': False,
                                'require-runtime-features': ['foo-bar'],
                            },
                            'bar': {'dependencies': ['bar']},
                        },
                    }
                }
            },
        }
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.dependencies == ['bar']


class TestFileSelectionDefaults:
    def test_include(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.default_include() == []

    def test_exclude(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.default_exclude() == []

    def test_packages(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.default_packages() == []

    def test_global_exclude(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.default_global_exclude() == ['*.py[cdo]', '/dist']


class TestPatternInclude:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.include_spec is None

    def test_global_becomes_spec(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ['foo']}}}}
        builder = Builder(str(isolation), config=config)

        assert isinstance(builder.config.include_spec, pathspec.GitIgnoreSpec)

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ''}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.include` must be an array of strings'):
            _ = builder.config.include_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_global(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'include': ['foo', 'bar/baz']}}}}
        builder = Builder(str(isolation), config=config)

        assert builder.config.include_spec.match_file(f'foo{separator}file.py')
        assert builder.config.include_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.include_spec.match_file(f'bar{separator}file.py')

    def test_global_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': [0]}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Pattern #1 in field `tool.hatch.build.include` must be a string'):
            _ = builder.config.include_spec

    def test_global_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ['']}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Pattern #1 in field `tool.hatch.build.include` cannot be an empty string'
        ):
            _ = builder.config.include_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_global_packages_included(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'packages': ['bar'], 'include': ['foo']}}}}
        builder = Builder(str(isolation), config=config)

        assert builder.config.include_spec.match_file(f'foo{separator}file.py')
        assert builder.config.include_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.include_spec.match_file(f'baz{separator}bar{separator}file.py')

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'include': ['foo', 'bar/baz']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.include_spec.match_file(f'foo{separator}file.py')
        assert builder.config.include_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.include_spec.match_file(f'bar{separator}file.py')

    def test_target_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'include': [0]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Pattern #1 in field `tool.hatch.build.targets.foo.include` must be a string'
        ):
            _ = builder.config.include_spec

    def test_target_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'include': ['']}}}}}}
        builder = Builder(str(isolation), config=config)
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
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert not builder.config.include_spec.match_file(f'foo{separator}file.py')
        assert builder.config.include_spec.match_file(f'bar{separator}file.py')

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target_packages_included(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'packages': ['bar'], 'include': ['foo']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.include_spec.match_file(f'foo{separator}file.py')
        assert builder.config.include_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.include_spec.match_file(f'baz{separator}bar{separator}file.py')


class TestPatternExclude:
    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_default(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        builder = Builder(str(isolation))

        assert isinstance(builder.config.exclude_spec, pathspec.GitIgnoreSpec)
        assert builder.config.exclude_spec.match_file(f'dist{separator}file.py')

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'exclude': ''}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.exclude` must be an array of strings'):
            _ = builder.config.exclude_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_global(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'exclude': ['foo', 'bar/baz']}}}}
        builder = Builder(str(isolation), config=config)

        assert builder.config.exclude_spec.match_file(f'foo{separator}file.py')
        assert builder.config.exclude_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.exclude_spec.match_file(f'bar{separator}file.py')

    def test_global_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'exclude': [0]}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Pattern #1 in field `tool.hatch.build.exclude` must be a string'):
            _ = builder.config.exclude_spec

    def test_global_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'exclude': ['']}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Pattern #1 in field `tool.hatch.build.exclude` cannot be an empty string'
        ):
            _ = builder.config.exclude_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'exclude': ['foo', 'bar/baz']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.exclude_spec.match_file(f'foo{separator}file.py')
        assert builder.config.exclude_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.exclude_spec.match_file(f'bar{separator}file.py')

    def test_target_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'exclude': [0]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Pattern #1 in field `tool.hatch.build.targets.foo.exclude` must be a string'
        ):
            _ = builder.config.exclude_spec

    def test_target_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'exclude': ['']}}}}}}
        builder = Builder(str(isolation), config=config)
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
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert not builder.config.exclude_spec.match_file(f'foo{separator}file.py')
        assert builder.config.exclude_spec.match_file(f'bar{separator}file.py')

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_vcs_git(self, temp_dir, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        with temp_dir.as_cwd():
            config = {'tool': {'hatch': {'build': {'exclude': ['foo']}}}}
            builder = Builder(str(temp_dir), config=config)

            vcs_ignore_file = temp_dir / '.gitignore'
            vcs_ignore_file.write_text('/bar\n*.pyc')

            assert builder.config.exclude_spec.match_file(f'foo{separator}file.py')
            assert builder.config.exclude_spec.match_file(f'bar{separator}file.py')
            assert builder.config.exclude_spec.match_file(f'baz{separator}bar{separator}file.pyc')
            assert not builder.config.exclude_spec.match_file(f'baz{separator}bar{separator}file.py')

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_ignore_vcs_git(self, temp_dir, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        with temp_dir.as_cwd():
            config = {'tool': {'hatch': {'build': {'ignore-vcs': True, 'exclude': ['foo']}}}}
            builder = Builder(str(temp_dir), config=config)

            vcs_ignore_file = temp_dir / '.gitignore'
            vcs_ignore_file.write_text('/bar\n*.pyc')

            assert builder.config.exclude_spec.match_file(f'foo{separator}file.py')
            assert not builder.config.exclude_spec.match_file(f'bar{separator}file.py')

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_vcs_mercurial(self, temp_dir, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        with temp_dir.as_cwd():
            config = {'tool': {'hatch': {'build': {'exclude': ['foo']}}}}
            builder = Builder(str(temp_dir), config=config)

            vcs_ignore_file = temp_dir / '.hgignore'
            vcs_ignore_file.write_text('syntax: glob\n/bar\n*.pyc')

            assert builder.config.exclude_spec.match_file(f'foo{separator}file.py')
            assert builder.config.exclude_spec.match_file(f'bar{separator}file.py')
            assert builder.config.exclude_spec.match_file(f'baz{separator}bar{separator}file.pyc')
            assert not builder.config.exclude_spec.match_file(f'baz{separator}bar{separator}file.py')

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_ignore_vcs_mercurial(self, temp_dir, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        with temp_dir.as_cwd():
            config = {'tool': {'hatch': {'build': {'ignore-vcs': True, 'exclude': ['foo']}}}}
            builder = Builder(str(temp_dir), config=config)

            vcs_ignore_file = temp_dir / '.hgignore'
            vcs_ignore_file.write_text('syntax: glob\n/bar\n*.pyc')

            assert builder.config.exclude_spec.match_file(f'foo{separator}file.py')
            assert not builder.config.exclude_spec.match_file(f'bar{separator}file.py')

    def test_override_default_global_exclude_patterns(self, isolation):
        builder = Builder(str(isolation))
        builder.config.default_global_exclude = lambda: []

        assert builder.config.exclude_spec is None
        assert not builder.config.path_is_excluded('.git/file')


class TestPatternArtifacts:
    def test_default(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.artifact_spec is None

    def test_global_becomes_spec(self, isolation):
        config = {'tool': {'hatch': {'build': {'artifacts': ['foo']}}}}
        builder = Builder(str(isolation), config=config)

        assert isinstance(builder.config.artifact_spec, pathspec.GitIgnoreSpec)

    def test_global_invalid_type(self, isolation):
        config = {'tool': {'hatch': {'build': {'artifacts': ''}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.artifacts` must be an array of strings'):
            _ = builder.config.artifact_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_global(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'artifacts': ['foo', 'bar/baz']}}}}
        builder = Builder(str(isolation), config=config)

        assert builder.config.artifact_spec.match_file(f'foo{separator}file.py')
        assert builder.config.artifact_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.artifact_spec.match_file(f'bar{separator}file.py')

    def test_global_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'artifacts': [0]}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Pattern #1 in field `tool.hatch.build.artifacts` must be a string'):
            _ = builder.config.artifact_spec

    def test_global_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'artifacts': ['']}}}}
        builder = Builder(str(isolation), config=config)

        with pytest.raises(
            ValueError, match='Pattern #1 in field `tool.hatch.build.artifacts` cannot be an empty string'
        ):
            _ = builder.config.artifact_spec

    @pytest.mark.parametrize('separator', ['/', '\\'])
    def test_target(self, isolation, separator, platform):
        if separator == '\\' and not platform.windows:
            pytest.skip('Not running on Windows')

        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'artifacts': ['foo', 'bar/baz']}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.config.artifact_spec.match_file(f'foo{separator}file.py')
        assert builder.config.artifact_spec.match_file(f'bar{separator}baz{separator}file.py')
        assert not builder.config.artifact_spec.match_file(f'bar{separator}file.py')

    def test_target_pattern_not_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'artifacts': [0]}}}}}}
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(
            TypeError, match='Pattern #1 in field `tool.hatch.build.targets.foo.artifacts` must be a string'
        ):
            _ = builder.config.artifact_spec

    def test_target_pattern_empty_string(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'artifacts': ['']}}}}}}
        builder = Builder(str(isolation), config=config)
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
        builder = Builder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert not builder.config.artifact_spec.match_file(f'foo{separator}file.py')
        assert builder.config.artifact_spec.match_file(f'bar{separator}file.py')


class TestPatternMatching:
    def test_include_explicit(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ['foo']}}}}
        builder = Builder(str(isolation), config=config)

        assert builder.config.include_path('foo/file.py')
        assert not builder.config.include_path('bar/file.py')

    def test_no_include_greedy(self, isolation):
        builder = Builder(str(isolation))

        assert builder.config.include_path('foo/file.py')
        assert builder.config.include_path('bar/file.py')

    def test_exclude_precedence(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ['foo'], 'exclude': ['foo']}}}}
        builder = Builder(str(isolation), config=config)

        assert not builder.config.include_path('foo/file.py')
        assert not builder.config.include_path('bar/file.py')

    def test_artifact_super_precedence(self, isolation):
        config = {'tool': {'hatch': {'build': {'include': ['foo'], 'exclude': ['foo'], 'artifacts': ['foo']}}}}
        builder = Builder(str(isolation), config=config)

        assert builder.config.include_path('foo/file.py')
        assert not builder.config.include_path('bar/file.py')
