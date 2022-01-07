from os.path import sep as path_sep

import pytest

from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.metadata.core import ProjectMetadata
from hatchling.plugin.manager import PluginManager


class TestClean:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))
        builder.clean(None, None)


class TestVersionAPI:
    def test_error(self, isolation):
        builder = BuilderInterface(str(isolation))

        with pytest.raises(NotImplementedError):
            builder.get_version_api()


class TestPluginManager:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert isinstance(builder.plugin_manager, PluginManager)

    def test_reuse(self, isolation):
        plugin_manager = PluginManager()
        builder = BuilderInterface(str(isolation), plugin_manager=plugin_manager)

        assert builder.plugin_manager is plugin_manager


class TestRawConfig:
    def test_default(self, isolation):
        builder = BuilderInterface(str(isolation))

        assert builder.raw_config == builder.raw_config == {}

    def test_reuse(self, isolation):
        config = {}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.raw_config is builder.raw_config is config

    def test_read(self, temp_dir):
        project_file = temp_dir / 'pyproject.toml'
        project_file.write_text('foo = 5')

        with temp_dir.as_cwd():
            builder = BuilderInterface(str(temp_dir))

            assert builder.raw_config == builder.raw_config == {'foo': 5}


class TestMetadata:
    def test_base(self, isolation):
        config = {'project': {'name': 'foo'}}
        builder = BuilderInterface(str(isolation), config=config)

        assert isinstance(builder.metadata, ProjectMetadata)
        assert builder.metadata.core.name == 'foo'

    def test_core(self, isolation):
        config = {'project': {}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.project_config is builder.project_config is config['project']

    def test_hatch(self, isolation):
        config = {'tool': {'hatch': {}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.hatch_config is builder.hatch_config is config['tool']['hatch']

    def test_build_config(self, isolation):
        config = {'tool': {'hatch': {'build': {}}}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.build_config is builder.build_config is config['tool']['hatch']['build']

    def test_build_config_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': 'foo'}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(TypeError, match='Field `tool.hatch.build` must be a table'):
            _ = builder.build_config

    def test_target_config(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        assert builder.target_config is builder.target_config is config['tool']['hatch']['build']['targets']['foo']

    def test_target_config_not_table(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': 'bar'}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets.foo` must be a table'):
            _ = builder.target_config


class TestProjectID:
    def test_normalization(self, isolation):
        config = {'project': {'name': 'my-app', 'version': '1.0.0-rc.1'}}
        builder = BuilderInterface(str(isolation), config=config)

        assert builder.project_id == builder.project_id == 'my_app-1.0.0rc1'


class TestVersions:
    def test_build_validation(self, isolation):
        config = {'tool': {'hatch': {'build': {'targets': {'foo': {'versions': ['1']}}}}}}
        builder = BuilderInterface(str(isolation), config=config)
        builder.PLUGIN_NAME = 'foo'
        builder.get_version_api = lambda: {'1': str}

        with pytest.raises(ValueError, match='Unknown versions for target `foo`: 42, 9000'):
            next(builder.build(str(isolation), versions=['9000', '42']))


class TestHookConfig:
    def test_unknown(self, isolation):
        config = {'tool': {'hatch': {'build': {'hooks': {'foo': {'bar': 'baz'}}}}}}
        builder = BuilderInterface(str(isolation), config=config)

        with pytest.raises(ValueError, match='Unknown build hook: foo'):
            _ = builder.get_build_hooks(str(isolation))


class TestDirectoryRecursion:
    def test_order(self, temp_dir):
        with temp_dir.as_cwd():
            config = {
                'tool': {
                    'hatch': {
                        'build': {
                            'packages': ['src/foo'],
                            'include': ['bar', 'README.md', 'tox.ini'],
                            'exclude': ['**/foo/baz.txt'],
                        }
                    }
                }
            }
            builder = BuilderInterface(str(temp_dir), config=config)

            foo = temp_dir / 'src' / 'foo'
            foo.ensure_dir_exists()
            (foo / 'bar.txt').touch()
            (foo / 'baz.txt').touch()

            bar = temp_dir / 'bar'
            bar.ensure_dir_exists()
            (bar / 'foo.txt').touch()

            (temp_dir / 'README.md').touch()
            (temp_dir / 'tox.ini').touch()

            assert [(f.path, f.distribution_path) for f in builder.recurse_project_files()] == [
                (str(temp_dir / 'README.md'), 'README.md'),
                (str(temp_dir / 'tox.ini'), 'tox.ini'),
                (
                    str(temp_dir / 'bar' / 'foo.txt'),
                    f'bar{path_sep}foo.txt',
                ),
                (str(temp_dir / 'src' / 'foo' / 'bar.txt'), f'foo{path_sep}bar.txt'),
            ]
