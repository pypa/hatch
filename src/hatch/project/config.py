import re
from copy import deepcopy
from itertools import product
from os import environ

from hatch.env.utils import ensure_valid_environment
from hatch.project.env import apply_overrides
from hatch.project.utils import format_script_commands, parse_script_command


class ProjectConfig:
    def __init__(self, root, config, plugin_manager=None):
        self.root = root
        self.config = config
        self.plugin_manager = plugin_manager

        self._matrices = None
        self._env = None
        self._env_collectors = None
        self._envs = None
        self._matrix_variables = None
        self._publish = None
        self._scripts = None
        self._cached_env_overrides = {}

    @property
    def env(self):
        if self._env is None:
            config = self.config.get('env', {})
            if not isinstance(config, dict):
                raise TypeError('Field `tool.hatch.env` must be a table')

            self._env = config

        return self._env

    @property
    def env_collectors(self):
        if self._env_collectors is None:
            collectors = self.env.get('collectors', {})
            if not isinstance(collectors, dict):
                raise TypeError('Field `tool.hatch.env.collectors` must be a table')

            final_config = {'default': {}}
            for collector, config in collectors.items():
                if not isinstance(config, dict):
                    raise TypeError(f'Field `tool.hatch.env.collectors.{collector}` must be a table')

                final_config[collector] = config

            self._env_collectors = final_config

        return self._env_collectors

    @property
    def matrices(self):
        if self._matrices is None:
            _ = self.envs

        return self._matrices

    @property
    def matrix_variables(self):
        if self._matrix_variables is None:
            _ = self.envs

        return self._matrix_variables

    @property
    def envs(self):
        from hatch.utils.platform import get_platform_name

        if self._envs is None:
            env_config = self.config.get('envs', {})
            if not isinstance(env_config, dict):
                raise TypeError('Field `tool.hatch.envs` must be a table')

            config = {}
            environment_collectors = []

            for collector, collector_config in self.env_collectors.items():
                collector_class = self.plugin_manager.environment_collector.get(collector)
                if collector_class is None:
                    from hatchling.plugin.exceptions import UnknownPluginError

                    raise UnknownPluginError(f'Unknown environment collector: {collector}')

                environment_collector = collector_class(self.root, collector_config)
                environment_collectors.append(environment_collector)

                for env_name, data in environment_collector.get_initial_config().items():
                    config.setdefault(env_name, data)

            for env_name, data in env_config.items():
                if not isinstance(data, dict):
                    raise TypeError(f'Field `tool.hatch.envs.{env_name}` must be a table')

                config.setdefault(env_name, {}).update(data)

            for environment_collector in environment_collectors:
                environment_collector.finalize_config(config)

            # Prevent plugins from removing the default environment
            ensure_valid_environment(config.setdefault('default', {}))

            seen = set()
            active = []
            for env_name, data in config.items():
                _populate_default_env_values(env_name, data, config, seen, active)

            current_platform = get_platform_name()
            all_matrices = {}
            generated_envs = {}
            final_config = {}
            cached_overrides = {}
            for env_name, initial_config in config.items():
                current_cached_overrides = cached_overrides[env_name] = {
                    'platform': [],
                    'env': [],
                    'matrix': [],
                    'name': [],
                }

                # Only shallow copying is necessary since we just want to modify keys
                initial_config = initial_config.copy()

                matrix_name_format = initial_config.pop('matrix-name-format', '{value}')
                if not isinstance(matrix_name_format, str):
                    raise TypeError(f'Field `tool.hatch.envs.{env_name}.matrix-name-format` must be a string')
                elif '{value}' not in matrix_name_format:
                    raise ValueError(
                        f'Field `tool.hatch.envs.{env_name}.matrix-name-format` must '
                        f'contain at least the `{{value}}` placeholder'
                    )

                overrides = initial_config.pop('overrides', {})
                if not isinstance(overrides, dict):
                    raise TypeError(f'Field `tool.hatch.envs.{env_name}.overrides` must be a table')

                # Apply any configuration based on the current platform
                platform_overrides = overrides.get('platform', {})
                if not isinstance(platform_overrides, dict):
                    raise TypeError(f'Field `tool.hatch.envs.{env_name}.overrides.platform` must be a table')

                for platform, options in platform_overrides.items():
                    if not isinstance(options, dict):
                        raise TypeError(
                            f'Field `tool.hatch.envs.{env_name}.overrides.platform.{platform}` must be a table'
                        )
                    elif platform != current_platform:
                        continue

                    apply_overrides(env_name, 'platform', platform, current_platform, options, initial_config)
                    current_cached_overrides['platform'].append((platform, current_platform, options))

                # Apply any configuration based on environment variables
                env_var_overrides = overrides.get('env', {})
                if not isinstance(env_var_overrides, dict):
                    raise TypeError(f'Field `tool.hatch.envs.{env_name}.overrides.env` must be a table')

                for env_var, options in env_var_overrides.items():
                    if not isinstance(options, dict):
                        raise TypeError(f'Field `tool.hatch.envs.{env_name}.overrides.env.{env_var}` must be a table')
                    elif env_var not in environ:
                        continue

                    apply_overrides(env_name, 'env', env_var, environ[env_var], options, initial_config)
                    current_cached_overrides['env'].append((env_var, environ[env_var], options))

                if 'matrix' not in initial_config:
                    final_config[env_name] = initial_config
                    continue

                matrices = initial_config.pop('matrix')
                if not isinstance(matrices, list):
                    raise TypeError(f'Field `tool.hatch.envs.{env_name}.matrix` must be an array')

                matrix_overrides = overrides.get('matrix', {})
                if not isinstance(matrix_overrides, dict):
                    raise TypeError(f'Field `tool.hatch.envs.{env_name}.overrides.matrix` must be a table')

                name_overrides = overrides.get('name', {})
                if not isinstance(name_overrides, dict):
                    raise TypeError(f'Field `tool.hatch.envs.{env_name}.overrides.name` must be a table')

                matrix_data = all_matrices[env_name] = {'config': deepcopy(initial_config)}
                all_envs = matrix_data['envs'] = {}
                for i, matrix in enumerate(matrices, 1):
                    if not isinstance(matrix, dict):
                        raise TypeError(f'Entry #{i} in field `tool.hatch.envs.{env_name}.matrix` must be a table')
                    elif not matrix:
                        raise ValueError(f'Matrix #{i} in field `tool.hatch.envs.{env_name}.matrix` cannot be empty')

                    for j, (variable, values) in enumerate(matrix.items(), 1):
                        if not variable:
                            raise ValueError(
                                f'Variable #{j} in matrix #{i} in field `tool.hatch.envs.{env_name}.matrix` '
                                f'cannot be an empty string'
                            )
                        elif not isinstance(values, list):
                            raise TypeError(
                                f'Variable `{variable}` in matrix #{i} in field `tool.hatch.envs.{env_name}.matrix` '
                                f'must be an array'
                            )
                        elif not values:
                            raise ValueError(
                                f'Variable `{variable}` in matrix #{i} in field `tool.hatch.envs.{env_name}.matrix` '
                                f'cannot be empty'
                            )

                        existing_values = set()
                        for k, value in enumerate(values, 1):
                            if not isinstance(value, str):
                                raise TypeError(
                                    f'Value #{k} of variable `{variable}` in matrix #{i} in field '
                                    f'`tool.hatch.envs.{env_name}.matrix` must be a string'
                                )
                            elif not value:
                                raise ValueError(
                                    f'Value #{k} of variable `{variable}` in matrix #{i} in field '
                                    f'`tool.hatch.envs.{env_name}.matrix` cannot be an empty string'
                                )
                            elif value in existing_values:
                                raise ValueError(
                                    f'Value #{k} of variable `{variable}` in matrix #{i} in field '
                                    f'`tool.hatch.envs.{env_name}.matrix` is a duplicate'
                                )
                            existing_values.add(value)

                    variables = {}

                    # Ensure that any Python variable comes first
                    python_selected = False
                    for variable in ('py', 'python'):
                        if variable in matrix:
                            if python_selected:
                                raise ValueError(
                                    f'Matrix #{i} in field `tool.hatch.envs.{env_name}.matrix` '
                                    f'cannot contain both `py` and `python` variables'
                                )
                            python_selected = True

                            # Only shallow copying is necessary since we just want to remove a key
                            matrix = matrix.copy()
                            variables[variable] = matrix.pop(variable)

                    variables.update(matrix)

                    for result in product(*variables.values()):
                        # Make a value mapping for easy referencing
                        variable_values = dict(zip(variables, result))

                        # Create the environment's initial configuration
                        new_config = deepcopy(initial_config)

                        cached_matrix_overrides = []

                        # Apply any configuration based on matrix variables
                        for variable, options in matrix_overrides.items():
                            if not isinstance(options, dict):
                                raise TypeError(
                                    f'Field `tool.hatch.envs.{env_name}.overrides.matrix.{variable}` must be a table'
                                )
                            elif variable not in variables:
                                continue

                            apply_overrides(
                                env_name, 'matrix', variable, variable_values[variable], options, new_config
                            )
                            cached_matrix_overrides.append((variable, variable_values[variable], options))

                        # Construct the environment name
                        final_matrix_name_format = new_config.pop('matrix-name-format', matrix_name_format)
                        env_name_parts = []
                        for j, (variable, value) in enumerate(variable_values.items()):
                            if j == 0 and python_selected:
                                new_config['python'] = value
                                env_name_parts.append(value if value.startswith('py') else f'py{value}')
                            else:
                                env_name_parts.append(final_matrix_name_format.format(variable=variable, value=value))

                        new_env_name = '-'.join(env_name_parts)

                        cached_name_overrides = []

                        # Apply any configuration based on the final name, minus the prefix for non-default environments
                        for pattern, options in name_overrides.items():
                            if not isinstance(options, dict):
                                raise TypeError(
                                    f'Field `tool.hatch.envs.{env_name}.overrides.name.{pattern}` must be a table'
                                )
                            elif not re.search(pattern, new_env_name):
                                continue

                            apply_overrides(env_name, 'name', pattern, new_env_name, options, new_config)
                            cached_name_overrides.append((pattern, new_env_name, options))

                        if env_name != 'default':
                            new_env_name = f'{env_name}.{new_env_name}'

                        # Save the generated environment
                        final_config[new_env_name] = new_config
                        cached_overrides[new_env_name] = {
                            'platform': current_cached_overrides['platform'],
                            'env': current_cached_overrides['env'],
                            'matrix': cached_matrix_overrides,
                            'name': cached_name_overrides,
                        }
                        all_envs[new_env_name] = variable_values
                        if 'py' in variable_values:
                            all_envs[new_env_name] = {'python': variable_values.pop('py'), **variable_values}

                # Remove the root matrix generator
                del cached_overrides[env_name]

                # Save the variables used to generate the environments
                generated_envs.update(all_envs)

            for environment_collector in environment_collectors:
                environment_collector.finalize_environments(final_config)

            self._matrices = all_matrices
            self._envs = final_config
            self._matrix_variables = generated_envs
            self._cached_env_overrides.update(cached_overrides)

        return self._envs

    @property
    def publish(self):
        if self._publish is None:
            config = self.config.get('publish', {})
            if not isinstance(config, dict):
                raise TypeError('Field `tool.hatch.publish` must be a table')

            for publisher, data in config.items():
                if not isinstance(data, dict):
                    raise TypeError(f'Field `tool.hatch.publish.{publisher}` must be a table')

            self._publish = config

        return self._publish

    @property
    def scripts(self):
        if self._scripts is None:
            script_config = self.config.get('scripts', {})
            if not isinstance(script_config, dict):
                raise TypeError('Field `tool.hatch.scripts` must be a table')

            config = {}

            for name, data in script_config.items():
                if ' ' in name:
                    raise ValueError(f'Script name `{name}` in field `tool.hatch.scripts` must not contain spaces')

                commands = []

                if isinstance(data, str):
                    commands.append(data)
                elif isinstance(data, list):
                    for i, command in enumerate(data, 1):
                        if not isinstance(command, str):
                            raise TypeError(f'Command #{i} in field `tool.hatch.scripts.{name}` must be a string')

                        commands.append(command)
                else:
                    raise TypeError(f'Field `tool.hatch.scripts.{name}` must be a string or an array of strings')

                config[name] = commands

            seen = {}
            active = []
            for script_name, commands in config.items():
                commands[:] = expand_script_commands(script_name, commands, config, seen, active)

            self._scripts = config

        return self._scripts

    def finalize_env_overrides(self, option_types):
        # We lazily apply overrides because we need type information potentially defined by
        # environment plugins for their options
        if not self._cached_env_overrides:
            return

        for env_name, config in self.envs.items():
            for override_name, data in self._cached_env_overrides[env_name].items():
                for condition, condition_value, options in data:
                    apply_overrides(env_name, override_name, condition, condition_value, options, config, option_types)

        self._cached_env_overrides.clear()


def expand_script_commands(script_name, commands, config, seen, active):
    if script_name in seen:
        return seen[script_name]
    elif script_name in active:
        active.append(script_name)
        raise ValueError(f'Circular expansion detected for field `tool.hatch.scripts`: {" -> ".join(active)}')

    active.append(script_name)

    expanded_commands = []

    for command in commands:
        possible_script, args, ignore_exit_code = parse_script_command(command)

        if possible_script in config:
            expanded_commands.extend(
                format_script_commands(
                    expand_script_commands(possible_script, config[possible_script], config, seen, active),
                    args,
                    ignore_exit_code,
                )
            )
        else:
            expanded_commands.append(command)

    seen[script_name] = expanded_commands
    active.pop()

    return expanded_commands


def _populate_default_env_values(env_name, data, config, seen, active):
    if env_name in seen:
        return
    elif data.pop('detached', False):
        data['template'] = env_name
        data['skip-install'] = True

    template_name = data.pop('template', 'default')
    if template_name not in config:
        raise ValueError(
            f'Field `tool.hatch.envs.{env_name}.template` refers to an unknown environment `{template_name}`'
        )
    elif env_name in active:
        active.append(env_name)
        raise ValueError(f'Circular inheritance detected for field `tool.hatch.envs.*.template`: {" -> ".join(active)}')
    elif template_name == env_name:
        ensure_valid_environment(data)
        seen.add(env_name)
        return

    active.append(env_name)

    template_config = config[template_name]
    _populate_default_env_values(template_name, template_config, config, seen, active)

    for key, value in template_config.items():
        if key == 'matrix':
            continue
        elif key == 'scripts':
            scripts = data['scripts'] if 'scripts' in data else data.setdefault('scripts', {})
            for script, commands in value.items():
                scripts.setdefault(script, commands)
        else:
            data.setdefault(key, value)

    seen.add(env_name)
    active.pop()
