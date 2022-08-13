from itertools import product

import pytest

from hatch.plugin.manager import PluginManager
from hatch.project.config import ProjectConfig
from hatch.project.env import RESERVED_OPTIONS
from hatch.utils.structures import EnvVars

ARRAY_OPTIONS = [o for o, t in RESERVED_OPTIONS.items() if t is list]
BOOLEAN_OPTIONS = [o for o, t in RESERVED_OPTIONS.items() if t is bool]
MAPPING_OPTIONS = [o for o, t in RESERVED_OPTIONS.items() if t is dict]
STRING_OPTIONS = [o for o, t in RESERVED_OPTIONS.items() if t is str and o != 'matrix-name-format']


def construct_matrix_data(env_name, config, overrides=None):
    config = dict(config[env_name])
    config.pop('overrides', None)
    matrices = config.pop('matrix')
    final_matrix_name_format = config.pop('matrix-name-format', '{value}')

    # [{'version': ['9000']}, {'feature': ['bar']}]
    envs = {}
    for matrix in matrices:
        matrix = dict(matrix)
        variables = {}
        python_selected = False
        for variable in ('py', 'python'):
            if variable in matrix:
                python_selected = True
                variables[variable] = matrix.pop(variable)
                break
        variables.update(matrix)

        for result in product(*variables.values()):
            variable_values = dict(zip(variables, result))
            env_name_parts = []
            for j, (variable, value) in enumerate(variable_values.items()):
                if j == 0 and python_selected:
                    env_name_parts.append(value if value.startswith('py') else f'py{value}')
                else:
                    env_name_parts.append(final_matrix_name_format.format(variable=variable, value=value))

            new_env_name = '-'.join(env_name_parts)
            if env_name != 'default':
                new_env_name = f'{env_name}.{new_env_name}'

            envs[new_env_name] = variable_values
            if 'py' in variable_values:
                envs[new_env_name] = {'python': variable_values.pop('py'), **variable_values}

    config.update(overrides or {})
    config.setdefault('type', 'virtual')
    return {'config': config, 'envs': envs}


class TestEnv:
    def test_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.env` must be a table'):
            _ = ProjectConfig(isolation, {'env': 9000}).env

    def test_default(self, isolation):
        project_config = ProjectConfig(isolation, {})

        assert project_config.env == project_config.env == {}


class TestEnvCollectors:
    def test_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.env.collectors` must be a table'):
            _ = ProjectConfig(isolation, {'env': {'collectors': 9000}}).env_collectors

    def test_collector_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.env.collectors.foo` must be a table'):
            _ = ProjectConfig(isolation, {'env': {'collectors': {'foo': 9000}}}).env_collectors

    def test_default(self, isolation):
        project_config = ProjectConfig(isolation, {})

        assert project_config.env_collectors == project_config.env_collectors == {'default': {}}

    def test_defined(self, isolation):
        project_config = ProjectConfig(isolation, {'env': {'collectors': {'foo': {'bar': {'baz': 9000}}}}})

        assert project_config.env_collectors == {'default': {}, 'foo': {'bar': {'baz': 9000}}}
        assert list(project_config.env_collectors) == ['default', 'foo']


class TestEnvs:
    def test_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs` must be a table'):
            _ = ProjectConfig(isolation, {'envs': 9000}, PluginManager()).envs

    def test_config_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo` must be a table'):
            _ = ProjectConfig(isolation, {'envs': {'foo': 9000}}, PluginManager()).envs

    def test_unknown_collector(self, isolation):
        with pytest.raises(ValueError, match='Unknown environment collector: foo'):
            _ = ProjectConfig(isolation, {'env': {'collectors': {'foo': {}}}}, PluginManager()).envs

    def test_unknown_template(self, isolation):
        with pytest.raises(
            ValueError, match='Field `tool.hatch.envs.foo.template` refers to an unknown environment `bar`'
        ):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'template': 'bar'}}}, PluginManager()).envs

    def test_default_undefined(self, isolation):
        project_config = ProjectConfig(isolation, {}, PluginManager())

        assert project_config.envs == project_config.envs == {'default': {'type': 'virtual'}}
        assert project_config.matrices == project_config.matrices == {}

    def test_default_partially_defined(self, isolation):
        env_config = {'default': {'option': True}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        assert project_config.envs == {'default': {'option': True, 'type': 'virtual'}}

    def test_default_defined(self, isolation):
        env_config = {'default': {'type': 'foo'}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        assert project_config.envs == {'default': {'type': 'foo'}}

    def test_basic(self, isolation):
        env_config = {'foo': {'option': True}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        assert project_config.envs == {'default': {'type': 'virtual'}, 'foo': {'option': True, 'type': 'virtual'}}

    def test_basic_override(self, isolation):
        env_config = {'foo': {'type': 'baz'}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        assert project_config.envs == {'default': {'type': 'virtual'}, 'foo': {'type': 'baz'}}

    def test_multiple_inheritance(self, isolation):
        env_config = {
            'foo': {'option1': 'foo'},
            'bar': {'template': 'foo', 'option2': 'bar'},
            'baz': {'template': 'bar', 'option3': 'baz'},
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        assert project_config.envs == {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'option1': 'foo'},
            'bar': {'type': 'virtual', 'option1': 'foo', 'option2': 'bar'},
            'baz': {'type': 'virtual', 'option1': 'foo', 'option2': 'bar', 'option3': 'baz'},
        }

    def test_circular_inheritance(self, isolation):
        with pytest.raises(
            ValueError, match='Circular inheritance detected for field `tool.hatch.envs.*.template`: foo -> bar -> foo'
        ):
            _ = ProjectConfig(
                isolation, {'envs': {'foo': {'template': 'bar'}, 'bar': {'template': 'foo'}}}, PluginManager()
            ).envs

    def test_scripts_inheritance(self, isolation):
        env_config = {
            'default': {'scripts': {'cmd1': 'bar', 'cmd2': 'baz'}},
            'foo': {'scripts': {'cmd1': 'foo'}},
            'bar': {'template': 'foo', 'scripts': {'cmd3': 'bar'}},
            'baz': {},
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        assert project_config.envs == {
            'default': {'type': 'virtual', 'scripts': {'cmd1': 'bar', 'cmd2': 'baz'}},
            'foo': {'type': 'virtual', 'scripts': {'cmd1': 'foo', 'cmd2': 'baz'}},
            'bar': {'type': 'virtual', 'scripts': {'cmd1': 'foo', 'cmd2': 'baz', 'cmd3': 'bar'}},
            'baz': {'type': 'virtual', 'scripts': {'cmd1': 'bar', 'cmd2': 'baz'}},
        }

    def test_self_referential(self, isolation):
        env_config = {'default': {'option1': 'foo'}, 'bar': {'template': 'bar'}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        assert project_config.envs == {
            'default': {'type': 'virtual', 'option1': 'foo'},
            'bar': {'type': 'virtual'},
        }

    def test_detached(self, isolation):
        env_config = {'default': {'option1': 'foo'}, 'bar': {'detached': True}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        assert project_config.envs == {
            'default': {'type': 'virtual', 'option1': 'foo'},
            'bar': {'type': 'virtual', 'skip-install': True},
        }

    def test_matrices_not_array(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.matrix` must be an array'):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix': 9000}}}, PluginManager()).envs

    def test_matrix_not_table(self, isolation):
        with pytest.raises(TypeError, match='Entry #1 in field `tool.hatch.envs.foo.matrix` must be a table'):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix': [9000]}}}, PluginManager()).envs

    def test_matrix_empty(self, isolation):
        with pytest.raises(ValueError, match='Matrix #1 in field `tool.hatch.envs.foo.matrix` cannot be empty'):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix': [{}]}}}, PluginManager()).envs

    def test_matrix_variable_empty_string(self, isolation):
        with pytest.raises(
            ValueError, match='Variable #1 in matrix #1 in field `tool.hatch.envs.foo.matrix` cannot be an empty string'
        ):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix': [{'': []}]}}}, PluginManager()).envs

    def test_matrix_variable_not_array(self, isolation):
        with pytest.raises(
            TypeError, match='Variable `bar` in matrix #1 in field `tool.hatch.envs.foo.matrix` must be an array'
        ):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix': [{'bar': 9000}]}}}, PluginManager()).envs

    def test_matrix_variable_array_empty(self, isolation):
        with pytest.raises(
            ValueError, match='Variable `bar` in matrix #1 in field `tool.hatch.envs.foo.matrix` cannot be empty'
        ):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix': [{'bar': []}]}}}, PluginManager()).envs

    def test_matrix_variable_entry_not_string(self, isolation):
        with pytest.raises(
            TypeError,
            match='Value #1 of variable `bar` in matrix #1 in field `tool.hatch.envs.foo.matrix` must be a string',
        ):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix': [{'bar': [9000]}]}}}, PluginManager()).envs

    def test_matrix_variable_entry_empty_string(self, isolation):
        with pytest.raises(
            ValueError,
            match=(
                'Value #1 of variable `bar` in matrix #1 in field `tool.hatch.envs.foo.matrix` '
                'cannot be an empty string'
            ),
        ):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix': [{'bar': ['']}]}}}, PluginManager()).envs

    def test_matrix_variable_entry_duplicate(self, isolation):
        with pytest.raises(
            ValueError,
            match='Value #2 of variable `bar` in matrix #1 in field `tool.hatch.envs.foo.matrix` is a duplicate',
        ):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix': [{'bar': ['1', '1']}]}}}, PluginManager()).envs

    def test_matrix_multiple_python_variables(self, isolation):
        with pytest.raises(
            ValueError,
            match='Matrix #1 in field `tool.hatch.envs.foo.matrix` cannot contain both `py` and `python` variables',
        ):
            _ = ProjectConfig(
                isolation,
                {'envs': {'foo': {'matrix': [{'py': ['39', '310'], 'python': ['39', '311']}]}}},
                PluginManager(),
            ).envs

    def test_matrix_name_format_not_string(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.matrix-name-format` must be a string'):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix-name-format': 9000}}}, PluginManager()).envs

    def test_matrix_name_format_invalid(self, isolation):
        with pytest.raises(
            ValueError,
            match='Field `tool.hatch.envs.foo.matrix-name-format` must contain at least the `{value}` placeholder',
        ):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'matrix-name-format': 'bar'}}}, PluginManager()).envs

    def test_overrides_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.overrides` must be a table'):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'overrides': 9000}}}, PluginManager()).envs

    def test_overrides_platform_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.overrides.platform` must be a table'):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'overrides': {'platform': 9000}}}}, PluginManager()).envs

    def test_overrides_env_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.overrides.env` must be a table'):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'overrides': {'env': 9000}}}}, PluginManager()).envs

    def test_overrides_matrix_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.overrides.matrix` must be a table'):
            _ = ProjectConfig(
                isolation,
                {'envs': {'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': 9000}}}},
                PluginManager(),
            ).envs

    def test_overrides_name_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.overrides.name` must be a table'):
            _ = ProjectConfig(
                isolation,
                {'envs': {'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'name': 9000}}}},
                PluginManager(),
            ).envs

    def test_overrides_platform_entry_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.overrides.platform.bar` must be a table'):
            _ = ProjectConfig(
                isolation, {'envs': {'foo': {'overrides': {'platform': {'bar': 9000}}}}}, PluginManager()
            ).envs

    def test_overrides_env_entry_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.overrides.env.bar` must be a table'):
            _ = ProjectConfig(isolation, {'envs': {'foo': {'overrides': {'env': {'bar': 9000}}}}}, PluginManager()).envs

    def test_overrides_matrix_entry_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.overrides.matrix.bar` must be a table'):
            _ = ProjectConfig(
                isolation,
                {'envs': {'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'bar': 9000}}}}},
                PluginManager(),
            ).envs

    def test_overrides_name_entry_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.envs.foo.overrides.name.bar` must be a table'):
            _ = ProjectConfig(
                isolation,
                {'envs': {'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'name': {'bar': 9000}}}}},
                PluginManager(),
            ).envs

    def test_matrix_simple_no_python(self, isolation):
        env_config = {'foo': {'option': True, 'matrix': [{'version': ['9000', '3.14']}]}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', 'option': True},
            'foo.3.14': {'type': 'virtual', 'option': True},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    def test_matrix_simple_no_python_custom_name_format(self, isolation):
        env_config = {
            'foo': {
                'option': True,
                'matrix-name-format': '{variable}_{value}',
                'matrix': [{'version': ['9000', '3.14']}],
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.version_9000': {'type': 'virtual', 'option': True},
            'foo.version_3.14': {'type': 'virtual', 'option': True},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('indicator', ['py', 'python'])
    def test_matrix_simple_only_python(self, isolation, indicator):
        env_config = {'foo': {'option': True, 'matrix': [{indicator: ['39', '310']}]}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.py39': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py310': {'type': 'virtual', 'option': True, 'python': '310'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('indicator', ['py', 'python'])
    def test_matrix_simple(self, isolation, indicator):
        env_config = {'foo': {'option': True, 'matrix': [{'version': ['9000', '3.14'], indicator: ['39', '310']}]}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.py39-9000': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py39-3.14': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py310-9000': {'type': 'virtual', 'option': True, 'python': '310'},
            'foo.py310-3.14': {'type': 'virtual', 'option': True, 'python': '310'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('indicator', ['py', 'python'])
    def test_matrix_simple_custom_name_format(self, isolation, indicator):
        env_config = {
            'foo': {
                'option': True,
                'matrix-name-format': '{variable}_{value}',
                'matrix': [{'version': ['9000', '3.14'], indicator: ['39', '310']}],
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.py39-version_9000': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py39-version_3.14': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py310-version_9000': {'type': 'virtual', 'option': True, 'python': '310'},
            'foo.py310-version_3.14': {'type': 'virtual', 'option': True, 'python': '310'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    def test_matrix_multiple_non_python(self, isolation):
        env_config = {
            'foo': {
                'option': True,
                'matrix': [{'version': ['9000', '3.14'], 'py': ['39', '310'], 'foo': ['baz', 'bar']}],
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.py39-9000-baz': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py39-9000-bar': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py39-3.14-baz': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py39-3.14-bar': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py310-9000-baz': {'type': 'virtual', 'option': True, 'python': '310'},
            'foo.py310-9000-bar': {'type': 'virtual', 'option': True, 'python': '310'},
            'foo.py310-3.14-baz': {'type': 'virtual', 'option': True, 'python': '310'},
            'foo.py310-3.14-bar': {'type': 'virtual', 'option': True, 'python': '310'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    def test_matrix_series(self, isolation):
        env_config = {
            'foo': {
                'option': True,
                'matrix': [
                    {'version': ['9000', '3.14'], 'py': ['39', '310'], 'foo': ['baz', 'bar']},
                    {'version': ['9000'], 'py': ['310'], 'baz': ['foo', 'test'], 'bar': ['foobar']},
                ],
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.py39-9000-baz': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py39-9000-bar': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py39-3.14-baz': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py39-3.14-bar': {'type': 'virtual', 'option': True, 'python': '39'},
            'foo.py310-9000-baz': {'type': 'virtual', 'option': True, 'python': '310'},
            'foo.py310-9000-bar': {'type': 'virtual', 'option': True, 'python': '310'},
            'foo.py310-3.14-baz': {'type': 'virtual', 'option': True, 'python': '310'},
            'foo.py310-3.14-bar': {'type': 'virtual', 'option': True, 'python': '310'},
            'foo.py310-9000-foo-foobar': {'type': 'virtual', 'option': True, 'python': '310'},
            'foo.py310-9000-test-foobar': {'type': 'virtual', 'option': True, 'python': '310'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    def test_matrices_not_inherited(self, isolation):
        env_config = {
            'foo': {'option1': True, 'matrix': [{'py': ['39']}]},
            'bar': {'template': 'foo', 'option2': False},
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.py39': {'type': 'virtual', 'option1': True, 'python': '39'},
            'bar': {'type': 'virtual', 'option1': True, 'option2': False},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    def test_matrix_default_naming(self, isolation):
        env_config = {'default': {'option': True, 'matrix': [{'version': ['9000', '3.14']}]}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            '9000': {'type': 'virtual', 'option': True},
            '3.14': {'type': 'virtual', 'option': True},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['default'] == construct_matrix_data('default', env_config)

    def test_matrix_pypy_naming(self, isolation):
        env_config = {'foo': {'option': True, 'matrix': [{'py': ['python3.9', 'pypy3']}]}}
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.python3.9': {'type': 'virtual', 'option': True, 'python': 'python3.9'},
            'foo.pypy3': {'type': 'virtual', 'option': True, 'python': 'pypy3'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_invalid_type(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=f'Field `tool.hatch.envs.foo.overrides.matrix.version.{option}` must be a string or an array',
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'version': {option: 9000}}}}
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_array_entry_invalid_type(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a string or an inline table'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [9000]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_table_entry_no_key(self, isolation, option):
        with pytest.raises(
            ValueError,
            match=(
                f'Entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must have an option named `key`'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'version': {option: [{}]}}}}
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_table_entry_key_not_string(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `key` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a string'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'key': 9000}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_table_entry_key_empty_string(self, isolation, option):
        with pytest.raises(
            ValueError,
            match=(
                f'Option `key` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'cannot be an empty string'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'key': ''}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_table_entry_value_not_string(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `value` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a string'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'key': 'foo', 'value': 9000}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_table_entry_if_not_array(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `if` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be an array'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {
                                'matrix': {'version': {option: [{'key': 'foo', 'value': 'bar', 'if': 9000}]}}
                            },
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_invalid_type(self, isolation, option):
        with pytest.raises(
            TypeError, match=f'Field `tool.hatch.envs.foo.overrides.matrix.version.{option}` must be an array'
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'version': {option: 9000}}}}
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_entry_no_value(self, isolation, option):
        with pytest.raises(
            ValueError,
            match=(
                f'Entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must have an option named `value`'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'version': {option: [{}]}}}}
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_entry_value_not_string(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `value` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a string'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': 9000}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_entry_value_empty_string(self, isolation, option):
        with pytest.raises(
            ValueError,
            match=(
                f'Option `value` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'cannot be an empty string'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': ''}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_entry_if_not_array(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `if` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be an array'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': 'foo', 'if': 9000}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_entry_invalid_type(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a string or an inline table'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [9000]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_invalid_type(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a string, inline table, or an array'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'version': {option: 9000}}}}
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_table_no_value(self, isolation, option):
        with pytest.raises(
            ValueError,
            match=f'Field `tool.hatch.envs.foo.overrides.matrix.version.{option}` must have an option named `value`',
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'version': {option: {}}}}}
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_table_value_not_string(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=f'Option `value` in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` must be a string',
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: {'value': 9000}}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_array_entry_invalid_type(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a string or an inline table'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [9000]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_array_table_no_value(self, isolation, option):
        with pytest.raises(
            ValueError,
            match=(
                f'Entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must have an option named `value`'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'version': {option: [{}]}}}}
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_array_table_value_not_string(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `value` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a string'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': 9000}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_array_table_if_not_array(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `if` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be an array'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': 'foo', 'if': 9000}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_invalid_type(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a boolean, inline table, or an array'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'version': {option: 9000}}}}
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_table_no_value(self, isolation, option):
        with pytest.raises(
            ValueError,
            match=f'Field `tool.hatch.envs.foo.overrides.matrix.version.{option}` must have an option named `value`',
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'version': {option: {}}}}}
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_table_value_not_boolean(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=f'Option `value` in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` must be a boolean',
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: {'value': 9000}}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_entry_invalid_type(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a boolean or an inline table'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [9000]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_no_value(self, isolation, option):
        with pytest.raises(
            ValueError,
            match=(
                f'Entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must have an option named `value`'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {'matrix': [{'version': ['9000']}], 'overrides': {'matrix': {'version': {option: [{}]}}}}
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_value_not_boolean(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `value` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be a boolean'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': 9000}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_if_not_array(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `if` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be an array'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': True, 'if': 9000}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_platform_not_array(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `platform` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be an array'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': True, 'platform': 9000}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_platform_item_not_string(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Item #1 in option `platform` in entry #1 in field '
                f'`tool.hatch.envs.foo.overrides.matrix.version.{option}` must be a string'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': True, 'platform': [9000]}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_env_not_array(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Option `env` in entry #1 in field `tool.hatch.envs.foo.overrides.matrix.version.{option}` '
                f'must be an array'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': True, 'env': 9000}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_env_item_not_string(self, isolation, option):
        with pytest.raises(
            TypeError,
            match=(
                f'Item #1 in option `env` in entry #1 in field '
                f'`tool.hatch.envs.foo.overrides.matrix.version.{option}` must be a string'
            ),
        ):
            _ = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000']}],
                            'overrides': {'matrix': {'version': {option: [{'value': True, 'env': [9000]}]}}},
                        }
                    }
                },
                PluginManager(),
            ).envs

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_string_with_value(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: 'FOO=ok'}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'FOO': 'ok'}},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_string_without_value(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: 'FOO'}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'FOO': '9000'}},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_string_override(self, isolation, option):
        env_config = {
            'foo': {
                option: {'TEST': 'baz'},
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: 'TEST'}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'TEST': '9000'}},
            'foo.bar': {'type': 'virtual', option: {'TEST': 'baz'}},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_array_string_with_value(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: ['FOO=ok']}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'FOO': 'ok'}},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_array_string_without_value(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: ['FOO']}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'FOO': '9000'}},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_array_string_override(self, isolation, option):
        env_config = {
            'foo': {
                option: {'TEST': 'baz'},
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: ['TEST']}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'TEST': '9000'}},
            'foo.bar': {'type': 'virtual', option: {'TEST': 'baz'}},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_array_table_key_with_value(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'key': 'FOO', 'value': 'ok'}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'FOO': 'ok'}},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_array_table_key_without_value(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'key': 'FOO'}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'FOO': '9000'}},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_array_table_override(self, isolation, option):
        env_config = {
            'foo': {
                option: {'TEST': 'baz'},
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'key': 'TEST'}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'TEST': '9000'}},
            'foo.bar': {'type': 'virtual', option: {'TEST': 'baz'}},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_array_table_conditional(self, isolation, option):
        env_config = {
            'foo': {
                option: {'TEST': 'baz'},
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'key': 'TEST', 'if': ['42']}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'TEST': 'baz'}},
            'foo.42': {'type': 'virtual', option: {'TEST': '42'}},
            'foo.bar': {'type': 'virtual', option: {'TEST': 'baz'}},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', MAPPING_OPTIONS)
    def test_overrides_matrix_mapping_overwrite(self, isolation, option):
        env_config = {
            'foo': {
                option: {'TEST': 'baz'},
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {f'set-{option}': ['FOO=bar', {'key': 'BAZ'}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: {'FOO': 'bar', 'BAZ': '9000'}},
            'foo.bar': {'type': 'virtual', option: {'TEST': 'baz'}},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_string(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: ['run foo']}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run foo']},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_string_existing_append(self, isolation, option):
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: ['run foo']}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run baz', 'run foo']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': 'run foo'}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run foo']},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_existing_append(self, isolation, option):
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': 'run foo'}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run baz', 'run foo']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_conditional(self, isolation, option):
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': 'run foo', 'if': ['42']}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run baz']},
            'foo.42': {'type': 'virtual', option: ['run baz', 'run foo']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_conditional_with_platform(self, isolation, option, current_platform):
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {
                    'matrix': {
                        'version': {option: [{'value': 'run foo', 'if': ['42'], 'platform': [current_platform]}]}
                    },
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run baz']},
            'foo.42': {'type': 'virtual', option: ['run baz', 'run foo']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_conditional_with_wrong_platform(self, isolation, option):
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {
                    'matrix': {'version': {option: [{'value': 'run foo', 'if': ['42'], 'platform': ['bar']}]}},
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run baz']},
            'foo.42': {'type': 'virtual', option: ['run baz']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_conditional_with_env_var_match(self, isolation, option):
        env_var = 'OVERRIDES_ENV_FOO'
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {
                    'matrix': {'version': {option: [{'value': 'run foo', 'if': ['42'], 'env': [f'{env_var}=bar']}]}}
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run baz']},
            'foo.42': {'type': 'virtual', option: ['run baz', 'run foo']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        with EnvVars({env_var: 'bar'}):
            assert project_config.envs == expected_envs
            assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_conditional_with_env_var_match_empty_string(self, isolation, option):
        env_var = 'OVERRIDES_ENV_FOO'
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {
                    'matrix': {'version': {option: [{'value': 'run foo', 'if': ['42'], 'env': [f'{env_var}=']}]}}
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run baz']},
            'foo.42': {'type': 'virtual', option: ['run baz', 'run foo']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        with EnvVars({env_var: ''}):
            assert project_config.envs == expected_envs
            assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_conditional_with_env_var_present(self, isolation, option):
        env_var = 'OVERRIDES_ENV_FOO'
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': 'run foo', 'if': ['42'], 'env': [env_var]}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run baz']},
            'foo.42': {'type': 'virtual', option: ['run baz', 'run foo']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        with EnvVars({env_var: 'any'}):
            assert project_config.envs == expected_envs
            assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_conditional_with_env_var_no_match(self, isolation, option):
        env_var = 'OVERRIDES_ENV_FOO'
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {
                    'matrix': {'version': {option: [{'value': 'run foo', 'if': ['42'], 'env': [f'{env_var}=bar']}]}}
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run baz']},
            'foo.42': {'type': 'virtual', option: ['run baz']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        with EnvVars({env_var: 'baz'}):
            assert project_config.envs == expected_envs
            assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_table_conditional_with_env_var_missing(self, isolation, option):
        env_var = 'OVERRIDES_ENV_FOO'
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {
                    'matrix': {'version': {option: [{'value': 'run foo', 'if': ['42'], 'env': [f'{env_var}=bar']}]}}
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run baz']},
            'foo.42': {'type': 'virtual', option: ['run baz']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    def test_overrides_matrix_set_with_no_type_information(self, isolation):
        env_var = 'OVERRIDES_ENV_FOO'
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {
                    'matrix': {'version': {'bar': {'value': ['baz'], 'if': ['42'], 'env': [f'{env_var}=bar']}}}
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual'},
            'foo.42': {'type': 'virtual', 'bar': ['baz']},
            'foo.bar': {'type': 'virtual'},
        }

        with EnvVars({env_var: 'bar'}):
            assert project_config.envs == expected_envs
            assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    def test_overrides_matrix_set_with_no_type_information_not_table(self, isolation):
        with pytest.raises(
            ValueError,
            match=(
                'Untyped option `tool.hatch.envs.foo.9000.overrides.matrix.version.bar` '
                'must be defined as a table with a `value` key'
            ),
        ):
            project_config = ProjectConfig(
                isolation,
                {
                    'envs': {
                        'foo': {
                            'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                            'overrides': {'matrix': {'version': {'bar': 9000}}},
                        }
                    }
                },
                PluginManager(),
            )
            _ = project_config.envs
            project_config.finalize_env_overrides({})

    @pytest.mark.parametrize('option', ARRAY_OPTIONS)
    def test_overrides_matrix_array_overwrite(self, isolation, option):
        env_config = {
            'foo': {
                option: ['run baz'],
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {f'set-{option}': ['run foo', {'value': 'run bar'}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: ['run foo', 'run bar']},
            'foo.bar': {'type': 'virtual', option: ['run baz']},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_string_create(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: 'baz'}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: 'baz'},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_string_overwrite(self, isolation, option):
        env_config = {
            'foo': {
                option: 'test',
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: 'baz'}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: 'baz'},
            'foo.bar': {'type': 'virtual', option: 'test'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_table_create(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: {'value': 'baz'}}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: 'baz'},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_table_override(self, isolation, option):
        env_config = {
            'foo': {
                option: 'test',
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: {'value': 'baz'}}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: 'baz'},
            'foo.bar': {'type': 'virtual', option: 'test'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_table_conditional(self, isolation, option):
        env_config = {
            'foo': {
                option: 'test',
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: {'value': 'baz', 'if': ['42']}}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: 'test'},
            'foo.42': {'type': 'virtual', option: 'baz'},
            'foo.bar': {'type': 'virtual', option: 'test'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_array_table_create(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': 'baz'}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: 'baz'},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_array_table_override(self, isolation, option):
        env_config = {
            'foo': {
                option: 'test',
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': 'baz'}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: 'baz'},
            'foo.bar': {'type': 'virtual', option: 'test'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_array_table_conditional(self, isolation, option):
        env_config = {
            'foo': {
                option: 'test',
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': 'baz', 'if': ['42']}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: 'test'},
            'foo.42': {'type': 'virtual', option: 'baz'},
            'foo.bar': {'type': 'virtual', option: 'test'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_array_table_conditional_eager_string(self, isolation, option):
        env_config = {
            'foo': {
                option: 'test',
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: ['baz', {'value': 'foo', 'if': ['42']}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: 'baz'},
            'foo.42': {'type': 'virtual', option: 'baz'},
            'foo.bar': {'type': 'virtual', option: 'test'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', STRING_OPTIONS)
    def test_overrides_matrix_string_array_table_conditional_eager_table(self, isolation, option):
        env_config = {
            'foo': {
                option: 'test',
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': 'baz', 'if': ['42']}, 'foo']}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: 'foo'},
            'foo.42': {'type': 'virtual', option: 'baz'},
            'foo.bar': {'type': 'virtual', option: 'test'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_boolean_create(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: True}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: True},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_boolean_overwrite(self, isolation, option):
        env_config = {
            'foo': {
                option: False,
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: True}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: True},
            'foo.bar': {'type': 'virtual', option: False},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_table_create(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: {'value': True}}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: True},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_table_override(self, isolation, option):
        env_config = {
            'foo': {
                option: False,
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: {'value': True}}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: True},
            'foo.bar': {'type': 'virtual', option: False},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_table_conditional(self, isolation, option):
        env_config = {
            'foo': {
                option: False,
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: {'value': True, 'if': ['42']}}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: False},
            'foo.42': {'type': 'virtual', option: True},
            'foo.bar': {'type': 'virtual', option: False},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_create(self, isolation, option):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': True}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: True},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_override(self, isolation, option):
        env_config = {
            'foo': {
                option: False,
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': True}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: True},
            'foo.bar': {'type': 'virtual', option: False},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_conditional(self, isolation, option):
        env_config = {
            'foo': {
                option: False,
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': True, 'if': ['42']}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: False},
            'foo.42': {'type': 'virtual', option: True},
            'foo.bar': {'type': 'virtual', option: False},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_conditional_eager_boolean(self, isolation, option):
        env_config = {
            'foo': {
                option: False,
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [True, {'value': False, 'if': ['42']}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: True},
            'foo.42': {'type': 'virtual', option: True},
            'foo.bar': {'type': 'virtual', option: False},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    @pytest.mark.parametrize('option', BOOLEAN_OPTIONS)
    def test_overrides_matrix_boolean_array_table_conditional_eager_table(self, isolation, option):
        env_config = {
            'foo': {
                option: False,
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {option: [{'value': True, 'if': ['42']}, False]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', option: False},
            'foo.42': {'type': 'virtual', option: True},
            'foo.bar': {'type': 'virtual', option: False},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    # We assert type coverage using matrix variable overrides, for the others just test one type
    def test_overrides_platform_boolean_boolean_create(self, isolation, current_platform):
        env_config = {
            'foo': {
                'overrides': {'platform': {'bar': {'dependencies': ['baz']}, current_platform: {'skip-install': True}}}
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'skip-install': True},
        }

        assert project_config.envs == expected_envs

    def test_overrides_platform_boolean_boolean_overwrite(self, isolation, current_platform):
        env_config = {
            'foo': {
                'skip-install': True,
                'overrides': {
                    'platform': {'bar': {'dependencies': ['baz']}, current_platform: {'skip-install': False}}
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'skip-install': False},
        }

        assert project_config.envs == expected_envs

    def test_overrides_platform_boolean_table_create(self, isolation, current_platform):
        env_config = {
            'foo': {
                'overrides': {
                    'platform': {
                        'bar': {'dependencies': ['baz']},
                        current_platform: {'skip-install': [{'value': True}]},
                    }
                }
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'skip-install': True},
        }

        assert project_config.envs == expected_envs

    def test_overrides_platform_boolean_table_overwrite(self, isolation, current_platform):
        env_config = {
            'foo': {
                'skip-install': True,
                'overrides': {
                    'platform': {
                        'bar': {'dependencies': ['baz']},
                        current_platform: {'skip-install': [{'value': False}]},
                    }
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'skip-install': False},
        }

        assert project_config.envs == expected_envs

    def test_overrides_env_boolean_boolean_create(self, isolation):
        env_var_exists = 'OVERRIDES_ENV_FOO'
        env_var_missing = 'OVERRIDES_ENV_BAR'
        env_config = {
            'foo': {
                'overrides': {
                    'env': {env_var_missing: {'dependencies': ['baz']}, env_var_exists: {'skip-install': True}}
                }
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'skip-install': True},
        }

        with EnvVars({env_var_exists: 'any'}):
            assert project_config.envs == expected_envs

    def test_overrides_env_boolean_boolean_overwrite(self, isolation):
        env_var_exists = 'OVERRIDES_ENV_FOO'
        env_var_missing = 'OVERRIDES_ENV_BAR'
        env_config = {
            'foo': {
                'skip-install': True,
                'overrides': {
                    'env': {env_var_missing: {'dependencies': ['baz']}, env_var_exists: {'skip-install': False}}
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'skip-install': False},
        }

        with EnvVars({env_var_exists: 'any'}):
            assert project_config.envs == expected_envs

    def test_overrides_env_boolean_table_create(self, isolation):
        env_var_exists = 'OVERRIDES_ENV_FOO'
        env_var_missing = 'OVERRIDES_ENV_BAR'
        env_config = {
            'foo': {
                'overrides': {
                    'env': {
                        env_var_missing: {'dependencies': ['baz']},
                        env_var_exists: {'skip-install': [{'value': True}]},
                    }
                }
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'skip-install': True},
        }

        with EnvVars({env_var_exists: 'any'}):
            assert project_config.envs == expected_envs

    def test_overrides_env_boolean_table_overwrite(self, isolation):
        env_var_exists = 'OVERRIDES_ENV_FOO'
        env_var_missing = 'OVERRIDES_ENV_BAR'
        env_config = {
            'foo': {
                'skip-install': True,
                'overrides': {
                    'env': {
                        env_var_missing: {'dependencies': ['baz']},
                        env_var_exists: {'skip-install': [{'value': False}]},
                    }
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'skip-install': False},
        }

        with EnvVars({env_var_exists: 'any'}):
            assert project_config.envs == expected_envs

    def test_overrides_env_boolean_conditional(self, isolation):
        env_var_exists = 'OVERRIDES_ENV_FOO'
        env_var_missing = 'OVERRIDES_ENV_BAR'
        env_config = {
            'foo': {
                'overrides': {
                    'env': {
                        env_var_missing: {'dependencies': ['baz']},
                        env_var_exists: {'skip-install': [{'value': True, 'if': ['foo']}]},
                    }
                }
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'skip-install': True},
        }

        with EnvVars({env_var_exists: 'foo'}):
            assert project_config.envs == expected_envs

    def test_overrides_name_boolean_boolean_create(self, isolation):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'name': {'bar$': {'skip-install': True}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual'},
            'foo.bar': {'type': 'virtual', 'skip-install': True},
        }

        assert project_config.envs == expected_envs

    def test_overrides_name_boolean_boolean_overwrite(self, isolation):
        env_config = {
            'foo': {
                'skip-install': True,
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'name': {'bar$': {'skip-install': False}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', 'skip-install': True},
            'foo.bar': {'type': 'virtual', 'skip-install': False},
        }

        assert project_config.envs == expected_envs

    def test_overrides_name_boolean_table_create(self, isolation):
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'name': {'bar$': {'skip-install': [{'value': True}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual'},
            'foo.bar': {'type': 'virtual', 'skip-install': True},
        }

        assert project_config.envs == expected_envs

    def test_overrides_name_boolean_table_overwrite(self, isolation):
        env_config = {
            'foo': {
                'skip-install': True,
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {'name': {'bar$': {'skip-install': [{'value': False}]}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', 'skip-install': True},
            'foo.bar': {'type': 'virtual', 'skip-install': False},
        }

        assert project_config.envs == expected_envs

    # Tests for source precedence
    def test_overrides_name_precedence_over_matrix(self, isolation):
        env_config = {
            'foo': {
                'skip-install': False,
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {
                    'name': {'42$': {'skip-install': False}},
                    'matrix': {'version': {'skip-install': [{'value': True, 'if': ['42']}]}},
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', 'skip-install': False},
            'foo.42': {'type': 'virtual', 'skip-install': False},
            'foo.bar': {'type': 'virtual', 'skip-install': False},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config, {'skip-install': False})

    def test_overrides_matrix_precedence_over_platform(self, isolation, current_platform):
        env_config = {
            'foo': {
                'skip-install': False,
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {
                    'platform': {current_platform: {'skip-install': True}},
                    'matrix': {'version': {'skip-install': [{'value': False, 'if': ['42']}]}},
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', 'skip-install': True},
            'foo.42': {'type': 'virtual', 'skip-install': False},
            'foo.bar': {'type': 'virtual', 'skip-install': True},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config, {'skip-install': True})

    def test_overrides_matrix_precedence_over_env(self, isolation):
        env_var = 'OVERRIDES_ENV_FOO'
        env_config = {
            'foo': {
                'skip-install': False,
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {
                    'env': {env_var: {'skip-install': True}},
                    'matrix': {'version': {'skip-install': [{'value': False, 'if': ['42']}]}},
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', 'skip-install': True},
            'foo.42': {'type': 'virtual', 'skip-install': False},
            'foo.bar': {'type': 'virtual', 'skip-install': True},
        }

        with EnvVars({env_var: 'any'}):
            assert project_config.envs == expected_envs
            assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config, {'skip-install': True})

    def test_overrides_env_precedence_over_platform(self, isolation, current_platform):
        env_var = 'OVERRIDES_ENV_FOO'
        env_config = {
            'foo': {
                'overrides': {
                    'platform': {current_platform: {'skip-install': True}},
                    'env': {env_var: {'skip-install': [{'value': False, 'if': ['foo']}]}},
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo': {'type': 'virtual', 'skip-install': False},
        }

        with EnvVars({env_var: 'foo'}):
            assert project_config.envs == expected_envs

    # Test for options defined by environment plugins
    def test_overrides_for_environment_plugins(self, isolation, current_platform):
        env_var = 'OVERRIDES_ENV_FOO'
        env_config = {
            'foo': {
                'matrix': [{'version': ['9000']}, {'feature': ['bar']}],
                'overrides': {
                    'platform': {current_platform: {'foo': True}},
                    'env': {env_var: {'bar': [{'value': 'foobar', 'if': ['foo']}]}},
                    'matrix': {'version': {'baz': 'BAR=ok'}},
                },
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual'},
            'foo.bar': {'type': 'virtual'},
        }

        with EnvVars({env_var: 'foo'}):
            assert project_config.envs == expected_envs
            assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

        project_config.finalize_env_overrides({'foo': bool, 'bar': str, 'baz': dict})

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual', 'foo': True, 'bar': 'foobar', 'baz': {'BAR': 'ok'}},
            'foo.bar': {'type': 'virtual', 'foo': True, 'bar': 'foobar'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)

    # Test environment collectors
    def test_environment_collector_finalize_config(self, isolation, mocker):
        def finalize_config(config):
            config['default']['type'] = 'foo'

        mocker.patch(
            'hatch.env.collectors.default.DefaultEnvironmentCollector.finalize_config',
            side_effect=finalize_config,
        )

        env_config = {
            'foo': {
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {'type': {'value': 'baz', 'if': ['42']}}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'foo'},
            'foo.9000': {'type': 'foo'},
            'foo.42': {'type': 'baz'},
            'foo.bar': {'type': 'foo'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config, {'type': 'foo'})

    def test_environment_collector_finalize_environments(self, isolation, mocker):
        def finalize_environments(config):
            config['foo.42']['type'] = 'foo'

        mocker.patch(
            'hatch.env.collectors.default.DefaultEnvironmentCollector.finalize_environments',
            side_effect=finalize_environments,
        )

        env_config = {
            'foo': {
                'matrix': [{'version': ['9000', '42']}, {'feature': ['bar']}],
                'overrides': {'matrix': {'version': {'type': {'value': 'baz', 'if': ['42']}}}},
            }
        }
        project_config = ProjectConfig(isolation, {'envs': env_config}, PluginManager())

        expected_envs = {
            'default': {'type': 'virtual'},
            'foo.9000': {'type': 'virtual'},
            'foo.42': {'type': 'foo'},
            'foo.bar': {'type': 'virtual'},
        }

        assert project_config.envs == expected_envs
        assert project_config.matrices['foo'] == construct_matrix_data('foo', env_config)


class TestPublish:
    def test_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.publish` must be a table'):
            _ = ProjectConfig(isolation, {'publish': 9000}).publish

    def test_config_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.publish.foo` must be a table'):
            _ = ProjectConfig(isolation, {'publish': {'foo': 9000}}).publish

    def test_default(self, isolation):
        project_config = ProjectConfig(isolation, {})

        assert project_config.publish == project_config.publish == {}

    def test_defined(self, isolation):
        project_config = ProjectConfig(isolation, {'publish': {'foo': {'bar': 'baz'}}})

        assert project_config.publish == {'foo': {'bar': 'baz'}}


class TestScripts:
    def test_not_table(self, isolation):
        config = {'scripts': 9000}
        project_config = ProjectConfig(isolation, config)

        with pytest.raises(TypeError, match='Field `tool.hatch.scripts` must be a table'):
            _ = project_config.scripts

    def test_name_contains_spaces(self, isolation):
        config = {'scripts': {'foo bar': []}}
        project_config = ProjectConfig(isolation, config)

        with pytest.raises(
            ValueError, match='Script name `foo bar` in field `tool.hatch.scripts` must not contain spaces'
        ):
            _ = project_config.scripts

    def test_default(self, isolation):
        project_config = ProjectConfig(isolation, {})

        assert project_config.scripts == project_config.scripts == {}

    def test_single_commands(self, isolation):
        config = {'scripts': {'foo': 'command1', 'bar': 'command2'}}
        project_config = ProjectConfig(isolation, config)

        assert project_config.scripts == {'foo': ['command1'], 'bar': ['command2']}

    def test_multiple_commands(self, isolation):
        config = {'scripts': {'foo': 'command1', 'bar': ['command3', 'command2']}}
        project_config = ProjectConfig(isolation, config)

        assert project_config.scripts == {'foo': ['command1'], 'bar': ['command3', 'command2']}

    def test_multiple_commands_not_string(self, isolation):
        config = {'scripts': {'foo': [9000]}}
        project_config = ProjectConfig(isolation, config)

        with pytest.raises(TypeError, match='Command #1 in field `tool.hatch.scripts.foo` must be a string'):
            _ = project_config.scripts

    def test_config_invalid_type(self, isolation):
        config = {'scripts': {'foo': 9000}}
        project_config = ProjectConfig(isolation, config)

        with pytest.raises(TypeError, match='Field `tool.hatch.scripts.foo` must be a string or an array of strings'):
            _ = project_config.scripts

    def test_command_expansion_basic(self, isolation):
        config = {'scripts': {'foo': 'command1', 'bar': ['command3', 'foo']}}
        project_config = ProjectConfig(isolation, config)

        assert project_config.scripts == {'foo': ['command1'], 'bar': ['command3', 'command1']}

    def test_command_expansion_multiple_nested(self, isolation):
        config = {
            'scripts': {
                'foo': 'command3',
                'baz': ['command5', 'bar', 'foo', 'command1'],
                'bar': ['command4', 'foo', 'command2'],
            }
        }
        project_config = ProjectConfig(isolation, config)

        assert project_config.scripts == {
            'foo': ['command3'],
            'baz': ['command5', 'command4', 'command3', 'command2', 'command3', 'command1'],
            'bar': ['command4', 'command3', 'command2'],
        }

    def test_command_expansion_multiple_nested_ignore_exit_code(self, isolation):
        config = {
            'scripts': {
                'foo': 'command3',
                'baz': ['command5', '- bar', 'foo', 'command1'],
                'bar': ['command4', '- foo', 'command2'],
            }
        }
        project_config = ProjectConfig(isolation, config)

        assert project_config.scripts == {
            'foo': ['command3'],
            'baz': ['command5', '- command4', '- command3', '- command2', 'command3', 'command1'],
            'bar': ['command4', '- command3', 'command2'],
        }

    def test_command_expansion_modification(self, isolation):
        config = {
            'scripts': {
                'foo': 'command3',
                'baz': ['command5', 'bar world', 'foo', 'command1'],
                'bar': ['command4', 'foo hello', 'command2'],
            }
        }
        project_config = ProjectConfig(isolation, config)

        assert project_config.scripts == {
            'foo': ['command3'],
            'baz': ['command5', 'command4 world', 'command3 hello world', 'command2 world', 'command3', 'command1'],
            'bar': ['command4', 'command3 hello', 'command2'],
        }

    def test_command_expansion_circular_inheritance(self, isolation):
        config = {'scripts': {'foo': 'bar', 'bar': 'foo'}}
        project_config = ProjectConfig(isolation, config)

        with pytest.raises(
            ValueError, match='Circular expansion detected for field `tool.hatch.scripts`: foo -> bar -> foo'
        ):
            _ = project_config.scripts
