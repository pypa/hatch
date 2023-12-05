from os.path import sep as path_sep

import pytest

from hatchling.builders.constants import EXCLUDED_DIRECTORIES
from hatchling.metadata.core import ProjectMetadata
from hatchling.plugin.manager import PluginManager

from ..utils import MockBuilder


class TestClean:
    def test_default(self, isolation):
        builder = MockBuilder(str(isolation))
        builder.clean(None, None)


class TestPluginManager:
    def test_default(self, isolation):
        builder = MockBuilder(str(isolation))

        assert isinstance(builder.plugin_manager, PluginManager)

    def test_reuse(self, isolation):
        plugin_manager = PluginManager()
        builder = MockBuilder(str(isolation), plugin_manager=plugin_manager)

        assert builder.plugin_manager is plugin_manager


class TestRawConfig:
    def test_default(self, isolation):
        builder = MockBuilder(str(isolation))

        assert builder.raw_config == builder.raw_config == {}

    def test_reuse(self, isolation):
        config = {}
        builder = MockBuilder(str(isolation), config=config)

        assert builder.raw_config is builder.raw_config is config

    def test_read(self, temp_dir):
        project_file = temp_dir / 'pyproject.toml'
        project_file.write_text('foo = 5')

        with temp_dir.as_cwd():
            builder = MockBuilder(str(temp_dir))

            assert builder.raw_config == builder.raw_config == {'foo': 5}


class TestMetadata:
    def test_base(self, isolation):
        config = {'project': {'name': 'foo'}}
        builder = MockBuilder(str(isolation), config=config)

        assert isinstance(builder.metadata, ProjectMetadata)
        assert builder.metadata.core.name == 'foo'

    def test_core(self, isolation):
        config = {'project': {}}
        builder = MockBuilder(str(isolation), config=config)

        assert builder.project_config is builder.project_config is config['project']

    def test_hatch(self, isolation):
        config = {'tool': {'hatch': {}}}
        builder = MockBuilder(str(isolation), config=config)

        assert builder.hatch_config is builder.hatch_config is config['tool']['hatch']

    def test_build_config(self, isolation):
        config = {'tool': {'hatch': {'build': {}}}}
        builder = MockBuilder(str(isolation), config=config)

        assert builder.build_config is builder.build_config is config['tool']['hatch']['build']

    def test_build_config_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': 'foo'}}}
        builder = MockBuilder(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build` must be a table'):
            _ = builder.build_config

    def test_target_config(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {}}}}}}
        builder = MockBuilder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.target_config is builder.target_config is config['tool']['hatch']['build']['targets']['foo']

    def test_target_config_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': 'bar'}}}}}
        builder = MockBuilder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo` must be a table'):
            _ = builder.target_config


class TestProjectID:
    def test_normalization(self, isolation):
        config = {'project': {'name': 'my-app', 'version': '1.0.0-rc.1'}}
        builder = MockBuilder(str(isolation), config=config)

        assert builder.project_id == builder.project_id == 'my_app-1.0.0rc1'


class TestBuildValidation:
    def test_unknown_version(self, isolation):
        config = {
            'project': {'name': 'foo', 'version': '0.1.0'},
            'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ['1']}}}}},
        }
        builder = MockBuilder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'
        builder.get_version_api = lambda: {'1': str}

        with pytest.raises(ValueError, match='Unknown versions for target `foo`: 42, 9000'):
            next(builder.build(directory=str(isolation), versions=['9000', '42']))

    def test_invalid_metadata(self, isolation):
        config = {
            'project': {'name': 'foo', 'version': '0.1.0', 'dynamic': ['version']},
            'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ['1']}}}}},
        }
        builder = MockBuilder(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'
        builder.get_version_api = lambda: {'1': lambda *_args, **_kwargs: ''}

        with pytest.raises(
            ValueError,
            match='Metadata field `version` cannot be both statically defined and listed in field `project.dynamic`',
        ):
            next(builder.build(directory=str(isolation)))


class TestHookConfig:
    def test_unknown(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'bar': 'baz'}}}}}}
        builder = MockBuilder(str(isolation), config=config)

        with pytest.raises(ValueError, match='Unknown build hook: foo'):
            _ = builder.get_build_hooks(str(isolation))


class TestDirectoryRecursion:
    @pytest.mark.requires_unix
    def test_infinite_loop_prevention(self, temp_dir):
        project_dir = temp_dir / 'project'
        project_dir.ensure_dir_exists()

        with project_dir.as_cwd():
            config = {'tool': {'hatch': {'build': {'include': ['foo', 'README.md']}}}}
            builder = MockBuilder(str(project_dir), config=config)

            (project_dir / 'README.md').touch()
            foo = project_dir / 'foo'
            foo.ensure_dir_exists()
            (foo / 'bar.txt').touch()

            (foo / 'baz').symlink_to(project_dir)

            assert [f.path for f in builder.recurse_included_files()] == [
                str(project_dir / 'README.md'),
                str(project_dir / 'foo' / 'bar.txt'),
            ]

    def test_only_include(self, temp_dir):
        project_dir = temp_dir / 'project'
        project_dir.ensure_dir_exists()

        with project_dir.as_cwd():
            config = {'tool': {'hatch': {'build': {'only-include': ['foo'], 'artifacts': ['README.md']}}}}
            builder = MockBuilder(str(project_dir), config=config)

            (project_dir / 'README.md').touch()
            foo = project_dir / 'foo'
            foo.ensure_dir_exists()
            (foo / 'bar.txt').touch()

            assert [f.path for f in builder.recurse_included_files()] == [str(project_dir / 'foo' / 'bar.txt')]

    def test_no_duplication_force_include_only(self, temp_dir):
        project_dir = temp_dir / 'project'
        project_dir.ensure_dir_exists()

        with project_dir.as_cwd():
            config = {
                'tool': {
                    'hatch': {
                        'build': {
                            'force-include': {
                                '../external.txt': 'new/target2.txt',
                                'old': 'new',
                            },
                        }
                    }
                }
            }
            builder = MockBuilder(str(project_dir), config=config)

            (project_dir / 'foo.txt').touch()
            old = project_dir / 'old'
            old.ensure_dir_exists()
            (old / 'target1.txt').touch()
            (old / 'target2.txt').touch()

            (temp_dir / 'external.txt').touch()

            build_data = builder.get_default_build_data()
            builder.set_build_data_defaults(build_data)
            with builder.config.set_build_data(build_data):
                assert [(f.path, f.distribution_path) for f in builder.recurse_included_files()] == [
                    (str(project_dir / 'foo.txt'), 'foo.txt'),
                    (str(project_dir / 'old' / 'target1.txt'), f'new{path_sep}target1.txt'),
                    (str(temp_dir / 'external.txt'), f'new{path_sep}target2.txt'),
                ]

    def test_no_duplication_force_include_and_selection(self, temp_dir):
        project_dir = temp_dir / 'project'
        project_dir.ensure_dir_exists()

        with project_dir.as_cwd():
            config = {
                'tool': {
                    'hatch': {
                        'build': {
                            'include': ['foo.txt', 'bar.txt', 'baz.txt'],
                            'force-include': {'../external.txt': 'new/file.txt'},
                        }
                    }
                }
            }
            builder = MockBuilder(str(project_dir), config=config)

            (project_dir / 'foo.txt').touch()
            (project_dir / 'bar.txt').touch()
            (project_dir / 'baz.txt').touch()
            (temp_dir / 'external.txt').touch()

            build_data = builder.get_default_build_data()
            builder.set_build_data_defaults(build_data)
            build_data['force_include']['bar.txt'] = 'bar.txt'

            with builder.config.set_build_data(build_data):
                assert [(f.path, f.distribution_path) for f in builder.recurse_included_files()] == [
                    (str(project_dir / 'baz.txt'), 'baz.txt'),
                    (str(project_dir / 'foo.txt'), 'foo.txt'),
                    (str(temp_dir / 'external.txt'), f'new{path_sep}file.txt'),
                    (str(project_dir / 'bar.txt'), 'bar.txt'),
                ]

    def test_no_duplication_force_include_with_sources(self, temp_dir):
        project_dir = temp_dir / 'project'
        project_dir.ensure_dir_exists()

        with project_dir.as_cwd():
            config = {
                'tool': {
                    'hatch': {
                        'build': {
                            'include': ['src'],
                            'sources': ['src'],
                            'force-include': {'../external.txt': 'new/file.txt'},
                        }
                    }
                }
            }
            builder = MockBuilder(str(project_dir), config=config)

            src_dir = project_dir / 'src'
            src_dir.mkdir()
            (src_dir / 'foo.txt').touch()
            (src_dir / 'bar.txt').touch()
            (src_dir / 'baz.txt').touch()
            (temp_dir / 'external.txt').touch()

            build_data = builder.get_default_build_data()
            builder.set_build_data_defaults(build_data)
            build_data['force_include']['src/bar.txt'] = 'bar.txt'

            with builder.config.set_build_data(build_data):
                assert [(f.path, f.distribution_path) for f in builder.recurse_included_files()] == [
                    (str(src_dir / 'baz.txt'), 'baz.txt'),
                    (str(src_dir / 'foo.txt'), 'foo.txt'),
                    (str(temp_dir / 'external.txt'), f'new{path_sep}file.txt'),
                    (str(src_dir / 'bar.txt'), 'bar.txt'),
                ]

    def test_exists(self, temp_dir):
        project_dir = temp_dir / 'project'
        project_dir.ensure_dir_exists()

        with project_dir.as_cwd():
            config = {
                'tool': {
                    'hatch': {
                        'build': {
                            'force-include': {
                                '../notfound': 'target.txt',
                            },
                        }
                    }
                }
            }
            builder = MockBuilder(str(project_dir), config=config)
            build_data = builder.get_default_build_data()
            builder.set_build_data_defaults(build_data)
            with builder.config.set_build_data(build_data), pytest.raises(
                FileNotFoundError, match='Forced include not found'
            ):
                list(builder.recurse_included_files())

    def test_order(self, temp_dir):
        project_dir = temp_dir / 'project'
        project_dir.ensure_dir_exists()

        with project_dir.as_cwd():
            config = {
                'tool': {
                    'hatch': {
                        'build': {
                            'sources': ['src'],
                            'include': ['src/foo', 'bar', 'README.md', 'tox.ini'],
                            'exclude': ['**/foo/baz.txt'],
                            'force-include': {
                                '../external1.txt': 'nested/target2.txt',
                                '../external2.txt': 'nested/target1.txt',
                                '../external': 'nested',
                            },
                        }
                    }
                }
            }
            builder = MockBuilder(str(project_dir), config=config)

            foo = project_dir / 'src' / 'foo'
            foo.ensure_dir_exists()
            (foo / 'bar.txt').touch()
            (foo / 'baz.txt').touch()

            bar = project_dir / 'bar'
            bar.ensure_dir_exists()
            (bar / 'foo.txt').touch()

            # Excluded
            for name in EXCLUDED_DIRECTORIES:
                excluded_dir = bar / name
                excluded_dir.ensure_dir_exists()
                (excluded_dir / 'file.ext').touch()

            (project_dir / 'README.md').touch()
            (project_dir / 'tox.ini').touch()

            (temp_dir / 'external1.txt').touch()
            (temp_dir / 'external2.txt').touch()

            external = temp_dir / 'external'
            external.ensure_dir_exists()
            (external / 'external1.txt').touch()
            (external / 'external2.txt').touch()

            # Excluded
            for name in EXCLUDED_DIRECTORIES:
                excluded_dir = external / name
                excluded_dir.ensure_dir_exists()
                (excluded_dir / 'file.ext').touch()

            assert [(f.path, f.distribution_path) for f in builder.recurse_included_files()] == [
                (str(project_dir / 'README.md'), 'README.md'),
                (str(project_dir / 'tox.ini'), 'tox.ini'),
                (
                    str(project_dir / 'bar' / 'foo.txt'),
                    f'bar{path_sep}foo.txt',
                ),
                (str(project_dir / 'src' / 'foo' / 'bar.txt'), f'foo{path_sep}bar.txt'),
                (str(temp_dir / 'external' / 'external1.txt'), f'nested{path_sep}external1.txt'),
                (str(temp_dir / 'external' / 'external2.txt'), f'nested{path_sep}external2.txt'),
                (str(temp_dir / 'external2.txt'), f'nested{path_sep}target1.txt'),
                (str(temp_dir / 'external1.txt'), f'nested{path_sep}target2.txt'),
            ]
