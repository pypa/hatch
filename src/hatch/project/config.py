from __future__ import annotations

import re
from copy import deepcopy
from itertools import product
from os import environ
from typing import TYPE_CHECKING

from hatch.env.utils import ensure_valid_environment
from hatch.project.env import apply_overrides
from hatch.project.utils import format_script_commands, parse_script_command

if TYPE_CHECKING:
    from packaging.requirements import Requirement


class ProjectConfig:
    def __init__(self, root, config, plugin_manager=None):
        self.root = root
        self.config = config
        self.plugin_manager = plugin_manager

        self._matrices = None
        self._env = None
        self._env_requires_complex = None
        self._env_requires = None
        self._env_collectors = None
        self._envs = None
        self._internal_envs = None
        self._internal_matrices = None
        self._matrix_variables = None
        self._publish = None
        self._scripts = None
        self._cached_env_overrides = {}

    @property
    def env(self):
        if self._env is None:
            config = self.config.get('env', {})
            if not isinstance(config, dict):
                message = 'Field `tool.hatch.env` must be a table'
                raise TypeError(message)

            self._env = config

        return self._env

    @property
    def env_requires_complex(self) -> list[Requirement]:
        if self._env_requires_complex is None:
            from packaging.requirements import InvalidRequirement, Requirement

            requires = self.env.get('requires', [])
            if not isinstance(requires, list):
                message = 'Field `tool.hatch.env.requires` must be an array'
                raise TypeError(message)

            requires_complex = []

            for i, entry in enumerate(requires, 1):
                if not isinstance(entry, str):
                    message = f'Requirement #{i} in `tool.hatch.env.requires` must be a string'
                    raise TypeError(message)

                try:
                    requires_complex.append(Requirement(entry))
                except InvalidRequirement as e:
                    message = f'Requirement #{i} in `tool.hatch.env.requires` is invalid: {e}'
                    raise ValueError(message) from None

            self._env_requires_complex = requires_complex

        return self._env_requires_complex

    @property
    def env_requires(self):
        if self._env_requires is None:
            self._env_requires = [str(r) for r in self.env_requires_complex]

        return self._env_requires

    @property
    def env_collectors(self):
        if self._env_collectors is None:
            collectors = self.env.get('collectors', {})
            if not isinstance(collectors, dict):
                message = 'Field `tool.hatch.env.collectors` must be a table'
                raise TypeError(message)

            final_config = {'default': {}}
            for collector, config in collectors.items():
                if not isinstance(config, dict):
                    message = f'Field `tool.hatch.env.collectors.{collector}` must be a table'
                    raise TypeError(message)

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
    def internal_envs(self):
        if self._internal_envs is None:
            _ = self.envs

        return self._internal_envs

    @property
    def internal_matrices(self):
        if self._internal_matrices is None:
            _ = self.envs

        return self._internal_matrices

    @property
    def envs(self):
        from hatch.env.internal import get_internal_env_config
        from hatch.utils.platform import get_platform_name

        if self._envs is None:
            env_config = self.config.get('envs', {})
            if not isinstance(env_config, dict):
                message = 'Field `tool.hatch.envs` must be a table'
                raise TypeError(message)

            config = {}
            environment_collectors = []

            for collector, collector_config in self.env_collectors.items():
                collector_class = self.plugin_manager.environment_collector.get(collector)
                if collector_class is None:
                    from hatchling.plugin.exceptions import UnknownPluginError

                    message = f'Unknown environment collector: {collector}'
                    raise UnknownPluginError(message)

                environment_collector = collector_class(self.root, collector_config)
                environment_collectors.append(environment_collector)

                for env_name, data in environment_collector.get_initial_config().items():
                    config.setdefault(env_name, data)

            for env_name, data in env_config.items():
                if not isinstance(data, dict):
                    message = f'Field `tool.hatch.envs.{env_name}` must be a table'
                    raise TypeError(message)

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
            for env_name, raw_initial_config in config.items():
                current_cached_overrides = cached_overrides[env_name] = {
                    'platform': [],
                    'env': [],
                    'matrix': [],
                    'name': [],
                }

                # Only shallow copying is necessary since we just want to modify keys
                initial_config = raw_initial_config.copy()

                matrix_name_format = initial_config.pop('matrix-name-format', '{value}')
                if not isinstance(matrix_name_format, str):
                    message = f'Field `tool.hatch.envs.{env_name}.matrix-name-format` must be a string'
                    raise TypeError(message)

                if '{value}' not in matrix_name_format:
                    message = (
                        f'Field `tool.hatch.envs.{env_name}.matrix-name-format` must '
                        f'contain at least the `{{value}}` placeholder'
                    )
                    raise ValueError(message)

                overrides = initial_config.pop('overrides', {})
                if not isinstance(overrides, dict):
                    message = f'Field `tool.hatch.envs.{env_name}.overrides` must be a table'
                    raise TypeError(message)

                # Apply any configuration based on the current platform
                platform_overrides = overrides.get('platform', {})
                if not isinstance(platform_overrides, dict):
                    message = f'Field `tool.hatch.envs.{env_name}.overrides.platform` must be a table'
                    raise TypeError(message)

                for platform, options in platform_overrides.items():
                    if not isinstance(options, dict):
                        message = f'Field `tool.hatch.envs.{env_name}.overrides.platform.{platform}` must be a table'
                        raise TypeError(message)

                    if platform != current_platform:
                        continue

                    apply_overrides(env_name, 'platform', platform, current_platform, options, initial_config)
                    current_cached_overrides['platform'].append((platform, current_platform, options))

                # Apply any configuration based on environment variables
                env_var_overrides = overrides.get('env', {})
                if not isinstance(env_var_overrides, dict):
                    message = f'Field `tool.hatch.envs.{env_name}.overrides.env` must be a table'
                    raise TypeError(message)

                for env_var, options in env_var_overrides.items():
                    if not isinstance(options, dict):
                        message = f'Field `tool.hatch.envs.{env_name}.overrides.env.{env_var}` must be a table'
                        raise TypeError(message)

                    if env_var not in environ:
                        continue

                    apply_overrides(env_name, 'env', env_var, environ[env_var], options, initial_config)
                    current_cached_overrides['env'].append((env_var, environ[env_var], options))

                if 'matrix' not in initial_config:
                    final_config[env_name] = initial_config
                    continue

                matrices = initial_config.pop('matrix')
                if not isinstance(matrices, list):
                    message = f'Field `tool.hatch.envs.{env_name}.matrix` must be an array'
                    raise TypeError(message)

                matrix_overrides = overrides.get('matrix', {})
                if not isinstance(matrix_overrides, dict):
                    message = f'Field `tool.hatch.envs.{env_name}.overrides.matrix` must be a table'
                    raise TypeError(message)

                name_overrides = overrides.get('name', {})
                if not isinstance(name_overrides, dict):
                    message = f'Field `tool.hatch.envs.{env_name}.overrides.name` must be a table'
                    raise TypeError(message)

                matrix_data = all_matrices[env_name] = {'config': deepcopy(initial_config)}
                all_envs = matrix_data['envs'] = {}
                for i, raw_matrix in enumerate(matrices, 1):
                    matrix = raw_matrix
                    if not isinstance(matrix, dict):
                        message = f'Entry #{i} in field `tool.hatch.envs.{env_name}.matrix` must be a table'
                        raise TypeError(message)

                    if not matrix:
                        message = f'Matrix #{i} in field `tool.hatch.envs.{env_name}.matrix` cannot be empty'
                        raise ValueError(message)

                    for j, (variable, values) in enumerate(matrix.items(), 1):
                        if not variable:
                            message = (
                                f'Variable #{j} in matrix #{i} in field `tool.hatch.envs.{env_name}.matrix` '
                                f'cannot be an empty string'
                            )
                            raise ValueError(message)

                        if not isinstance(values, list):
                            message = (
                                f'Variable `{variable}` in matrix #{i} in field `tool.hatch.envs.{env_name}.matrix` '
                                f'must be an array'
                            )
                            raise TypeError(message)

                        if not values:
                            message = (
                                f'Variable `{variable}` in matrix #{i} in field `tool.hatch.envs.{env_name}.matrix` '
                                f'cannot be empty'
                            )
                            raise ValueError(message)

                        existing_values = set()
                        for k, value in enumerate(values, 1):
                            if not isinstance(value, str):
                                message = (
                                    f'Value #{k} of variable `{variable}` in matrix #{i} in field '
                                    f'`tool.hatch.envs.{env_name}.matrix` must be a string'
                                )
                                raise TypeError(message)

                            if not value:
                                message = (
                                    f'Value #{k} of variable `{variable}` in matrix #{i} in field '
                                    f'`tool.hatch.envs.{env_name}.matrix` cannot be an empty string'
                                )
                                raise ValueError(message)

                            if value in existing_values:
                                message = (
                                    f'Value #{k} of variable `{variable}` in matrix #{i} in field '
                                    f'`tool.hatch.envs.{env_name}.matrix` is a duplicate'
                                )
                                raise ValueError(message)

                            existing_values.add(value)

                    variables = {}

                    # Ensure that any Python variable comes first
                    python_selected = False
                    for variable in ('py', 'python'):
                        if variable in matrix:
                            if python_selected:
                                message = (
                                    f'Matrix #{i} in field `tool.hatch.envs.{env_name}.matrix` '
                                    f'cannot contain both `py` and `python` variables'
                                )
                                raise ValueError(message)
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
                                message = (
                                    f'Field `tool.hatch.envs.{env_name}.overrides.matrix.{variable}` must be a table'
                                )
                                raise TypeError(message)

                            if variable not in variables:
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
                                message = f'Field `tool.hatch.envs.{env_name}.overrides.name.{pattern}` must be a table'
                                raise TypeError(message)

                            if not re.search(pattern, new_env_name):
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
            self._internal_matrices = {}
            self._envs = final_config
            self._matrix_variables = generated_envs
            self._cached_env_overrides.update(cached_overrides)

            # Extract the internal environments
            self._internal_envs = {}
            for internal_name in get_internal_env_config():
                try:
                    self._internal_envs[internal_name] = self._envs.pop(internal_name)
                # Matrix
                except KeyError:
                    self._internal_matrices[internal_name] = self._matrices.pop(internal_name)
                    for env_name in [env_name for env_name in self._envs if env_name.startswith(f'{internal_name}.')]:
                        self._internal_envs[env_name] = self._envs.pop(env_name)

        return self._envs

    @property
    def publish(self):
        if self._publish is None:
            config = self.config.get('publish', {})
            if not isinstance(config, dict):
                message = 'Field `tool.hatch.publish` must be a table'
                raise TypeError(message)

            for publisher, data in config.items():
                if not isinstance(data, dict):
                    message = f'Field `tool.hatch.publish.{publisher}` must be a table'
                    raise TypeError(message)

            self._publish = config

        return self._publish

    @property
    def scripts(self):
        if self._scripts is None:
            script_config = self.config.get('scripts', {})
            if not isinstance(script_config, dict):
                message = 'Field `tool.hatch.scripts` must be a table'
                raise TypeError(message)

            config = {}

            for name, data in script_config.items():
                if ' ' in name:
                    message = f'Script name `{name}` in field `tool.hatch.scripts` must not contain spaces'
                    raise ValueError(message)

                commands = []

                if isinstance(data, str):
                    commands.append(data)
                elif isinstance(data, list):
                    for i, command in enumerate(data, 1):
                        if not isinstance(command, str):
                            message = f'Command #{i} in field `tool.hatch.scripts.{name}` must be a string'
                            raise TypeError(message)

                        commands.append(command)
                else:
                    message = f'Field `tool.hatch.scripts.{name}` must be a string or an array of strings'
                    raise TypeError(message)

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

        for environments in (self.envs, self.internal_envs):
            for env_name, config in environments.items():
                for override_name, data in self._cached_env_overrides.get(env_name, {}).items():
                    for condition, condition_value, options in data:
                        apply_overrides(
                            env_name, override_name, condition, condition_value, options, config, option_types
                        )

        self._cached_env_overrides.clear()


def expand_script_commands(script_name, commands, config, seen, active):
    if script_name in seen:
        return seen[script_name]

    if script_name in active:
        active.append(script_name)

        message = f'Circular expansion detected for field `tool.hatch.scripts`: {" -> ".join(active)}'
        raise ValueError(message)

    active.append(script_name)

    expanded_commands = []

    for command in commands:
        possible_script, args, ignore_exit_code = parse_script_command(command)

        if possible_script in config:
            expanded_commands.extend(
                format_script_commands(
                    commands=expand_script_commands(possible_script, config[possible_script], config, seen, active),
                    args=args,
                    ignore_exit_code=ignore_exit_code,
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

    if data.pop('detached', False):
        data['template'] = env_name
        data['skip-install'] = True

    template_name = data.pop('template', 'default')
    if template_name not in config:
        message = f'Field `tool.hatch.envs.{env_name}.template` refers to an unknown environment `{template_name}`'
        raise ValueError(message)

    if env_name in active:
        active.append(env_name)

        message = f'Circular inheritance detected for field `tool.hatch.envs.*.template`: {" -> ".join(active)}'
        raise ValueError(message)

    if template_name == env_name:
        ensure_valid_environment(data)
        seen.add(env_name)
        return

    active.append(env_name)

    template_config = config[template_name]
    _populate_default_env_values(template_name, template_config, config, seen, active)

    for key, value in template_config.items():
        if key == 'matrix':
            continue

        if key == 'scripts':
            scripts = data['scripts'] if 'scripts' in data else data.setdefault('scripts', {})
            for script, commands in value.items():
                scripts.setdefault(script, commands)
        else:
            data.setdefault(key, value)

    seen.add(env_name)
    active.pop()
