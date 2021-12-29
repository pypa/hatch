import pytest

from hatch.config.constants import AppEnvVars
from hatch.env.plugin.interface import EnvironmentInterface
from hatch.project.core import Project


class MockEnvironment(EnvironmentInterface):
    def create(self):
        pass

    def remove(self):
        pass

    def exists(self):
        pass

    def install_project(self):
        pass

    def install_project_dev_mode(self):
        pass

    def dependencies_in_sync(self):
        pass

    def sync_dependencies(self):
        pass


class TestEnvVars:
    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1'}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.env_vars == environment.env_vars == {AppEnvVars.ENV_ACTIVE: 'default'}

    def test_not_table(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'env-vars': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.env-vars` must be a mapping'):
            _ = environment.env_vars

    def test_value_not_string(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'env-vars': {'foo': 9000}}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            TypeError, match='Environment variable `foo` of field `tool.hatch.envs.default.env-vars` must be a string'
        ):
            _ = environment.env_vars

    def test_correct(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'env-vars': {'foo': 'bar'}}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.env_vars == {AppEnvVars.ENV_ACTIVE: 'default', 'foo': 'bar'}


class TestEnvInclude:
    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1'}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.env_include == environment.env_include == []

    def test_not_array(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'env-include': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.env-include` must be an array'):
            _ = environment.env_include

    def test_pattern_not_string(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'env-include': [9000]}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            TypeError, match='Pattern #1 of field `tool.hatch.envs.default.env-include` must be a string'
        ):
            _ = environment.env_include

    def test_correct(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'env-include': ['FOO*']}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.env_include == ['HATCH_BUILD_*', 'FOO*']


class TestEnvExclude:
    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1'}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.env_exclude == environment.env_exclude == []

    def test_not_array(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'env-exclude': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.env-exclude` must be an array'):
            _ = environment.env_exclude

    def test_pattern_not_string(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'env-exclude': [9000]}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            TypeError, match='Pattern #1 of field `tool.hatch.envs.default.env-exclude` must be a string'
        ):
            _ = environment.env_exclude

    def test_correct(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'env-exclude': ['FOO*']}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.env_exclude == ['FOO*']


class TestPlatforms:
    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1'}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.platforms == environment.platforms == []

    def test_not_array(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'platforms': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.platforms` must be an array'):
            _ = environment.platforms

    def test_entry_not_string(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'platforms': [9000]}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            TypeError, match='Platform #1 of field `tool.hatch.envs.default.platforms` must be a string'
        ):
            _ = environment.platforms

    def test_correct(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'platforms': ['macOS']}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.platforms == ['macos']


class TestSkipInstall:
    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1'}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.skip_install is environment.skip_install is False

    def test_not_boolean(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'skip-install': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.skip-install` must be a boolean'):
            _ = environment.skip_install

    def test_enable(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'skip-install': True}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.skip_install is True


class TestDevMode:
    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1'}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.dev_mode is environment.dev_mode is True

    def test_not_boolean(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'dev-mode': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.dev-mode` must be a boolean'):
            _ = environment.dev_mode

    def test_disable(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'dev-mode': False}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.dev_mode is False


class TestFeature:
    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1'}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.features == environment.features == []

    def test_invalid_type(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'features': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.features` must be an array of strings'):
            _ = environment.features

    def test_correct(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'optional-dependencies': {'foo': [], 'bar': []}},
            'tool': {'hatch': {'envs': {'default': {'features': ['foo', 'bar']}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.features == ['foo', 'bar']

    def test_feature_not_string(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'optional-dependencies': {'foo': [], 'bar': []}},
            'tool': {'hatch': {'envs': {'default': {'features': [9000]}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Feature #1 of field `tool.hatch.envs.default.features` must be a string'):
            _ = environment.features

    def test_feature_empty_string(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'optional-dependencies': {'foo': [], 'bar': []}},
            'tool': {'hatch': {'envs': {'default': {'features': ['']}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            ValueError, match='Feature #1 of field `tool.hatch.envs.default.features` cannot be an empty string'
        ):
            _ = environment.features

    def test_feature_undefined(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'optional-dependencies': {'foo': []}},
            'tool': {'hatch': {'envs': {'default': {'features': ['foo', 'bar', '']}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            ValueError,
            match=(
                'Feature `bar` of field `tool.hatch.envs.default.features` is not defined in '
                'field `project.optional-dependencies`'
            ),
        ):
            _ = environment.features


class TestDependencies:
    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1', 'dependencies': ['dep1']}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.dependencies == environment.dependencies == ['dep1']
        assert len(environment.dependencies) == len(environment.dependencies_complex)

    def test_not_array(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'dependencies': ['dep1']},
            'tool': {'hatch': {'envs': {'default': {'dependencies': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.dependencies` must be an array'):
            _ = environment.dependencies

    def test_entry_not_string(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'dependencies': ['dep1']},
            'tool': {'hatch': {'envs': {'default': {'dependencies': [9000]}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            TypeError, match='Dependency #1 of field `tool.hatch.envs.default.dependencies` must be a string'
        ):
            _ = environment.dependencies

    def test_invalid_specifier(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'dependencies': ['dep1']},
            'tool': {'hatch': {'envs': {'default': {'dependencies': ['foo^1']}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            ValueError, match='Dependency #1 of field `tool.hatch.envs.default.dependencies` is invalid: .+'
        ):
            _ = environment.dependencies

    def test_full(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'dependencies': ['dep1']},
            'tool': {'hatch': {'envs': {'default': {'dependencies': ['dep2']}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.dependencies == ['dep2', 'dep1']

    def test_full_skip_install(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'dependencies': ['dep1']},
            'tool': {'hatch': {'envs': {'default': {'dependencies': ['dep2'], 'skip-install': True}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.dependencies == ['dep2']

    def test_full_dev_mode(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1', 'dependencies': ['dep1']},
            'tool': {'hatch': {'envs': {'default': {'dependencies': ['dep2'], 'dev-mode': False}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.dependencies == ['dep2']


class TestScripts:
    def test_not_table(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'scripts': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.scripts` must be a table'):
            _ = environment.scripts

    def test_name_contains_spaces(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'scripts': {'foo bar': []}}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            ValueError, match='Script name `foo bar` in field `tool.hatch.envs.default.scripts` must not contain spaces'
        ):
            _ = environment.scripts

    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1'}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.scripts == environment.scripts == {}

    def test_single_commands(self, isolation, data_dir, platform):
        script_config = {'foo': 'command1', 'bar': 'command2'}
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'scripts': script_config}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.scripts == {'foo': ['command1'], 'bar': ['command2']}

    def test_multiple_commands(self, isolation, data_dir, platform):
        script_config = {'foo': 'command1', 'bar': ['command3', 'command2']}
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'scripts': script_config}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.scripts == {'foo': ['command1'], 'bar': ['command3', 'command2']}

    def test_multiple_commands_not_string(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'scripts': {'foo': [9000]}}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            TypeError, match='Command #1 in field `tool.hatch.envs.default.scripts.foo` must be a string'
        ):
            _ = environment.scripts

    def test_config_invalid_type(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'scripts': {'foo': 9000}}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            TypeError, match='Field `tool.hatch.envs.default.scripts.foo` must be a string or an array of strings'
        ):
            _ = environment.scripts

    def test_command_expansion_basic(self, isolation, data_dir, platform):
        script_config = {'foo': 'command1', 'bar': ['command3', 'foo']}
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'scripts': script_config}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.scripts == {'foo': ['command1'], 'bar': ['command3', 'command1']}

    def test_command_expansion_multiple_nested(self, isolation, data_dir, platform):
        script_config = {
            'foo': 'command3',
            'baz': ['command5', 'bar', 'foo', 'command1'],
            'bar': ['command4', 'foo', 'command2'],
        }
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'scripts': script_config}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.scripts == {
            'foo': ['command3'],
            'baz': ['command5', 'command4', 'command3', 'command2', 'command3', 'command1'],
            'bar': ['command4', 'command3', 'command2'],
        }

    def test_command_expansion_modification(self, isolation, data_dir, platform):
        script_config = {
            'foo': 'command3',
            'baz': ['command5', 'bar world', 'foo', 'command1'],
            'bar': ['command4', 'foo hello', 'command2'],
        }
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'scripts': script_config}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.scripts == {
            'foo': ['command3'],
            'baz': ['command5', 'command4 world', 'command3 hello world', 'command2 world', 'command3', 'command1'],
            'bar': ['command4', 'command3 hello', 'command2'],
        }

    def test_command_expansion_circular_inheritance(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'scripts': {'foo': 'bar', 'bar': 'foo'}}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            ValueError,
            match='Circular expansion detected for field `tool.hatch.envs.default.scripts`: foo -> bar -> foo',
        ):
            _ = environment.scripts


class TestPreInstallCommands:
    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1'}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.pre_install_commands == environment.pre_install_commands == []

    def test_not_array(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'pre-install-commands': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.pre-install-commands` must be an array'):
            _ = environment.pre_install_commands

    def test_entry_not_string(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'pre-install-commands': [9000]}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            TypeError, match='Command #1 of field `tool.hatch.envs.default.pre-install-commands` must be a string'
        ):
            _ = environment.pre_install_commands

    def test_correct(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'pre-install-commands': ['baz test']}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.pre_install_commands == ['baz test']


class TestPostInstallCommands:
    def test_default(self, isolation, data_dir, platform):
        config = {'project': {'name': 'my_app', 'version': '0.0.1'}}
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.post_install_commands == environment.post_install_commands == []

    def test_not_array(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'post-install-commands': 9000}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(TypeError, match='Field `tool.hatch.envs.default.post-install-commands` must be an array'):
            _ = environment.post_install_commands

    def test_entry_not_string(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'post-install-commands': [9000]}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        with pytest.raises(
            TypeError, match='Command #1 of field `tool.hatch.envs.default.post-install-commands` must be a string'
        ):
            _ = environment.post_install_commands

    def test_correct(self, isolation, data_dir, platform):
        config = {
            'project': {'name': 'my_app', 'version': '0.0.1'},
            'tool': {'hatch': {'envs': {'default': {'post-install-commands': ['baz test']}}}},
        }
        project = Project(isolation, config=config)
        environment = MockEnvironment(
            isolation, project.metadata, 'default', project.config.envs['default'], data_dir, platform, 0
        )

        assert environment.post_install_commands == ['baz test']
