from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from os.path import isabs

from hatch.config.constants import AppEnvVars
from hatch.env.utils import add_verbosity_flag
from hatch.project.utils import format_script_commands, parse_script_command
from hatch.utils.structures import EnvVars


class EnvironmentInterface(ABC):
    """
    Example usage:

    === ":octicons-file-code-16: plugin.py"

        ```python
        from hatch.env.plugin.interface import EnvironmentInterface


        class SpecialEnvironment(EnvironmentInterface):
            PLUGIN_NAME = 'special'
            ...
        ```

    === ":octicons-file-code-16: hooks.py"

        ```python
        from hatchling.plugin import hookimpl

        from .plugin import SpecialEnvironment


        @hookimpl
        def hatch_register_environment():
            return SpecialEnvironment
        ```
    """

    PLUGIN_NAME = ''
    """The name used for selection."""

    def __init__(self, root, metadata, name, config, matrix_variables, data_directory, platform, verbosity, app=None):
        self.__root = root
        self.__metadata = metadata
        self.__name = name
        self.__config = config
        self.__matrix_variables = matrix_variables
        self.__data_directory = data_directory
        self.__platform = platform
        self.__verbosity = verbosity
        self.__app = app
        self.__context = None

        self._system_python = None
        self._env_vars = None
        self._env_include = None
        self._env_exclude = None
        self._environment_dependencies_complex = None
        self._environment_dependencies = None
        self._dependencies_complex = None
        self._dependencies = None
        self._platforms = None
        self._skip_install = None
        self._dev_mode = None
        self._features = None
        self._description = None
        self._scripts = None
        self._pre_install_commands = None
        self._post_install_commands = None

    @property
    def matrix_variables(self):
        return self.__matrix_variables

    @property
    def app(self):
        """
        An instance of [Application](../utilities.md#hatchling.bridge.app.Application).
        """
        if self.__app is None:
            from hatchling.bridge.app import Application

            self.__app = Application().get_safe_application()

        return self.__app

    @property
    def context(self):
        if self.__context is None:
            self.__context = self.get_context()

        return self.__context

    @property
    def verbosity(self):
        return self.__verbosity

    @property
    def root(self):
        """
        The root of the project tree as a path-like object.
        """
        return self.__root

    @property
    def metadata(self):
        return self.__metadata

    @property
    def name(self) -> str:
        """
        The name of the environment.
        """
        return self.__name

    @property
    def platform(self):
        """
        An instance of [Platform](../utilities.md#hatch.utils.platform.Platform).
        """
        return self.__platform

    @property
    def data_directory(self):
        """
        The [directory](../../config/hatch.md#environments) reserved exclusively for this plugin as a path-like object.
        """
        return self.__data_directory

    @property
    def config(self) -> dict:
        """
        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.envs.<ENV_NAME>]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [envs.<ENV_NAME>]
            ```
        """
        return self.__config

    @property
    def system_python(self):
        if self._system_python is None:
            system_python = os.environ.get(AppEnvVars.PYTHON)
            if system_python == 'self':
                system_python = sys.executable

            system_python = (
                system_python
                or self.platform.modules.shutil.which('python')
                or self.platform.modules.shutil.which('python3')
                or sys.executable
            )
            if not isabs(system_python):
                system_python = self.platform.modules.shutil.which(system_python)

            self._system_python = system_python

        return self._system_python

    @property
    def env_vars(self) -> dict:
        """
        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.envs.<ENV_NAME>.env-vars]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [envs.<ENV_NAME>.env-vars]
            ```
        """
        if self._env_vars is None:
            env_vars = self.config.get('env-vars', {})
            if not isinstance(env_vars, dict):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.env-vars` must be a mapping')

            for key, value in env_vars.items():
                if not isinstance(value, str):
                    raise TypeError(
                        f'Environment variable `{key}` of field `tool.hatch.envs.{self.name}.env-vars` must be a string'
                    )

            new_env_vars = {}
            with self.metadata.context.apply_context(self.context):
                for key, value in env_vars.items():
                    new_env_vars[key] = self.metadata.context.format(value)

            new_env_vars[AppEnvVars.ENV_ACTIVE] = self.name
            self._env_vars = new_env_vars

        return self._env_vars

    @property
    def env_include(self) -> list[str]:
        """
        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.envs.<ENV_NAME>]
            env-include = [...]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [envs.<ENV_NAME>]
            env-include = [...]
            ```
        """
        if self._env_include is None:
            env_include = self.config.get('env-include', [])
            if not isinstance(env_include, list):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.env-include` must be an array')

            for i, pattern in enumerate(env_include, 1):
                if not isinstance(pattern, str):
                    raise TypeError(f'Pattern #{i} of field `tool.hatch.envs.{self.name}.env-include` must be a string')

            if env_include:
                self._env_include = ['HATCH_BUILD_*', *env_include]
            else:
                self._env_include = env_include

        return self._env_include

    @property
    def env_exclude(self) -> list[str]:
        """
        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.envs.<ENV_NAME>]
            env-exclude = [...]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [envs.<ENV_NAME>]
            env-exclude = [...]
            ```
        """
        if self._env_exclude is None:
            env_exclude = self.config.get('env-exclude', [])
            if not isinstance(env_exclude, list):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.env-exclude` must be an array')

            for i, pattern in enumerate(env_exclude, 1):
                if not isinstance(pattern, str):
                    raise TypeError(f'Pattern #{i} of field `tool.hatch.envs.{self.name}.env-exclude` must be a string')

            self._env_exclude = env_exclude

        return self._env_exclude

    @property
    def environment_dependencies_complex(self):
        if self._environment_dependencies_complex is None:
            from packaging.requirements import InvalidRequirement, Requirement

            dependencies_complex = []
            with self.apply_context():
                for option in ('dependencies', 'extra-dependencies'):
                    dependencies = self.config.get(option, [])
                    if not isinstance(dependencies, list):
                        raise TypeError(f'Field `tool.hatch.envs.{self.name}.{option}` must be an array')

                    for i, entry in enumerate(dependencies, 1):
                        if not isinstance(entry, str):
                            raise TypeError(
                                f'Dependency #{i} of field `tool.hatch.envs.{self.name}.{option}` must be a string'
                            )

                        try:
                            dependencies_complex.append(Requirement(self.metadata.context.format(entry)))
                        except InvalidRequirement as e:
                            raise ValueError(
                                f'Dependency #{i} of field `tool.hatch.envs.{self.name}.{option}` is invalid: {e}'
                            )

            self._environment_dependencies_complex = dependencies_complex

        return self._environment_dependencies_complex

    @property
    def environment_dependencies(self) -> list[str]:
        """
        The list of all [environment dependencies](../../config/environment/overview.md#dependencies).
        """
        if self._environment_dependencies is None:
            self._environment_dependencies = [str(dependency) for dependency in self.environment_dependencies_complex]

        return self._environment_dependencies

    @property
    def dependencies_complex(self):
        if self._dependencies_complex is None:
            all_dependencies_complex = list(self.environment_dependencies_complex)

            # Ensure these are checked last to speed up initial environment creation since
            # they will already be installed along with the project
            if not self.skip_install and self.dev_mode:
                from hatch.utils.dep import get_project_dependencies_complex

                dependencies_complex, optional_dependencies_complex = get_project_dependencies_complex(self)

                all_dependencies_complex.extend(dependencies_complex.values())

                for feature in self.features:
                    if feature not in optional_dependencies_complex:
                        raise ValueError(
                            f'Feature `{feature}` of field `tool.hatch.envs.{self.name}.features` is not '
                            f'defined in the dynamic field `project.optional-dependencies`'
                        )

                    all_dependencies_complex.extend(optional_dependencies_complex[feature].values())

            self._dependencies_complex = all_dependencies_complex

        return self._dependencies_complex

    @property
    def dependencies(self) -> list[str]:
        """
        The list of all [project dependencies](../../config/metadata.md#dependencies) (if
        [installed](../../config/environment/overview.md#skip-install) and in
        [dev mode](../../config/environment/overview.md#dev-mode)) and
        [environment dependencies](../../config/environment/overview.md#dependencies).
        """
        if self._dependencies is None:
            self._dependencies = [str(dependency) for dependency in self.dependencies_complex]

        return self._dependencies

    @property
    def platforms(self) -> list[str]:
        """
        All names are stored as their lower-cased version.

        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.envs.<ENV_NAME>]
            platforms = [...]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [envs.<ENV_NAME>]
            platforms = [...]
            ```
        """
        if self._platforms is None:
            platforms = self.config.get('platforms', [])
            if not isinstance(platforms, list):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.platforms` must be an array')

            for i, command in enumerate(platforms, 1):
                if not isinstance(command, str):
                    raise TypeError(f'Platform #{i} of field `tool.hatch.envs.{self.name}.platforms` must be a string')

            self._platforms = [platform.lower() for platform in platforms]

        return self._platforms

    @property
    def skip_install(self) -> bool:
        """
        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.envs.<ENV_NAME>]
            skip-install = ...
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [envs.<ENV_NAME>]
            skip-install = ...
            ```
        """
        if self._skip_install is None:
            skip_install = self.config.get('skip-install', not self.metadata.has_project_file())
            if not isinstance(skip_install, bool):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.skip-install` must be a boolean')

            self._skip_install = skip_install

        return self._skip_install

    @property
    def dev_mode(self) -> bool:
        """
        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.envs.<ENV_NAME>]
            dev-mode = ...
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [envs.<ENV_NAME>]
            dev-mode = ...
            ```
        """
        if self._dev_mode is None:
            dev_mode = self.config.get('dev-mode', True)
            if not isinstance(dev_mode, bool):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.dev-mode` must be a boolean')

            self._dev_mode = dev_mode

        return self._dev_mode

    @property
    def features(self):
        if self._features is None:
            from hatchling.metadata.utils import normalize_project_name

            features = self.config.get('features', [])
            if not isinstance(features, list):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.features` must be an array of strings')

            all_features = set()
            for i, feature in enumerate(features, 1):
                if not isinstance(feature, str):
                    raise TypeError(f'Feature #{i} of field `tool.hatch.envs.{self.name}.features` must be a string')
                elif not feature:
                    raise ValueError(
                        f'Feature #{i} of field `tool.hatch.envs.{self.name}.features` cannot be an empty string'
                    )

                if not self.metadata.hatch.metadata.allow_ambiguous_features:
                    feature = normalize_project_name(feature)
                if (
                    not self.metadata.hatch.metadata.hook_config
                    and feature not in self.metadata.core.optional_dependencies
                ):
                    raise ValueError(
                        f'Feature `{feature}` of field `tool.hatch.envs.{self.name}.features` is not '
                        f'defined in field `project.optional-dependencies`'
                    )

                all_features.add(feature)

            self._features = sorted(all_features)

        return self._features

    @property
    def description(self) -> str:
        """
        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.envs.<ENV_NAME>]
            description = ...
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [envs.<ENV_NAME>]
            description = ...
            ```
        """
        if self._description is None:
            description = self.config.get('description', '')
            if not isinstance(description, str):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.description` must be a string')

            self._description = description

        return self._description

    @property
    def scripts(self):
        if self._scripts is None:
            script_config = self.config.get('scripts', {})
            if not isinstance(script_config, dict):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.scripts` must be a table')

            config = {}

            for name, data in script_config.items():
                if ' ' in name:
                    raise ValueError(
                        f'Script name `{name}` in field `tool.hatch.envs.{self.name}.scripts` must not contain spaces'
                    )

                commands = []

                if isinstance(data, str):
                    commands.append(data)
                elif isinstance(data, list):
                    for i, command in enumerate(data, 1):
                        if not isinstance(command, str):
                            raise TypeError(
                                f'Command #{i} in field `tool.hatch.envs.{self.name}.scripts.{name}` must be a string'
                            )

                        commands.append(command)
                else:
                    raise TypeError(
                        f'Field `tool.hatch.envs.{self.name}.scripts.{name}` must be a string or an array of strings'
                    )

                config[name] = commands

            seen = {}
            active = []
            for script_name, commands in config.items():
                commands[:] = expand_script_commands(self.name, script_name, commands, config, seen, active)

            self._scripts = config

        return self._scripts

    @property
    def pre_install_commands(self):
        if self._pre_install_commands is None:
            pre_install_commands = self.config.get('pre-install-commands', [])
            if not isinstance(pre_install_commands, list):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.pre-install-commands` must be an array')

            for i, command in enumerate(pre_install_commands, 1):
                if not isinstance(command, str):
                    raise TypeError(
                        f'Command #{i} of field `tool.hatch.envs.{self.name}.pre-install-commands` must be a string'
                    )

            self._pre_install_commands = list(pre_install_commands)

        return self._pre_install_commands

    @property
    def post_install_commands(self):
        if self._post_install_commands is None:
            post_install_commands = self.config.get('post-install-commands', [])
            if not isinstance(post_install_commands, list):
                raise TypeError(f'Field `tool.hatch.envs.{self.name}.post-install-commands` must be an array')

            for i, command in enumerate(post_install_commands, 1):
                if not isinstance(command, str):
                    raise TypeError(
                        f'Command #{i} of field `tool.hatch.envs.{self.name}.post-install-commands` must be a string'
                    )

            self._post_install_commands = list(post_install_commands)

        return self._post_install_commands

    def activate(self):
        """
        A convenience method called when using the environment as a context manager:

        ```python
        with environment:
            ...
        ```
        """

    def deactivate(self):
        """
        A convenience method called after using the environment as a context manager:

        ```python
        with environment:
            ...
        ```
        """

    @abstractmethod
    def find(self):
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        This should return information about how to locate the environment.
        """

    @abstractmethod
    def create(self):
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        This should perform the necessary steps to set up the environment.
        """

    @abstractmethod
    def remove(self):
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        This should perform the necessary steps to completely remove the environment from the system and will only
        be triggered manually by users with the [`env remove`](../../cli/reference.md#hatch-env-remove) or
        [`env prune`](../../cli/reference.md#hatch-env-prune) commands.

        If the
        [build environment](reference.md#hatch.env.plugin.interface.EnvironmentInterface.build_environment)
        has a caching mechanism, this should remove that as well.
        """

    @abstractmethod
    def exists(self) -> bool:
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        This should indicate whether or not the environment has already been created.
        """

    @abstractmethod
    def install_project(self):
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        This should install the project in the environment.
        """

    @abstractmethod
    def install_project_dev_mode(self):
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        This should install the project in the environment such that the environment
        always reflects the current state of the project.
        """

    @abstractmethod
    def dependencies_in_sync(self) -> bool:
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        This should indicate whether or not the environment is compatible with the current
        [dependencies](reference.md#hatch.env.plugin.interface.EnvironmentInterface.dependencies).
        """

    @abstractmethod
    def sync_dependencies(self):
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        This should install the
        [dependencies](reference.md#hatch.env.plugin.interface.EnvironmentInterface.dependencies)
        in the environment.
        """

    @contextmanager
    def build_environment(self, dependencies: list[str]):
        """
        This should set up an isolated environment in which to [`build`](../../cli/reference.md#hatch-build) the project
        given a set of dependencies and must be a context manager:

        ```python
        with environment.build_environment([...]):
            ...
        ```

        The build environment should reflect any
        [environment variables](reference.md#hatch.env.plugin.interface.EnvironmentInterface.get_env_vars)
        the user defined either currently or at the time of
        [creation](reference.md#hatch.env.plugin.interface.EnvironmentInterface.create).
        """
        with self.get_env_vars():
            yield

    def get_build_process(self, build_environment, **kwargs):
        """
        This will be called when the
        [build environment](reference.md#hatch.env.plugin.interface.EnvironmentInterface.build_environment)
        is active:

        ```python
        with environment.build_environment([...]) as build_environment:
            build_process = environment.get_build_process(build_environment, ...)
        ```

        This should return the standard library's
        [subprocess.Popen](https://docs.python.org/3/library/subprocess.html#subprocess.Popen)
        with all output captured by `stdout`. The command is constructed by passing all keyword arguments to
        [construct_build_command](reference.md#hatch.env.plugin.interface.EnvironmentInterface.construct_build_command).

        For an example, open the default implementation below:
        """
        return self.platform.capture_process(self.construct_build_command(**kwargs))

    def build_environment_exists(self):
        """
        If the
        [build environment](reference.md#hatch.env.plugin.interface.EnvironmentInterface.build_environment)
        has a caching mechanism, this should indicate whether or not it has already been created.
        """
        return False

    def enter_shell(self, name, path, args):
        """
        Spawn a [shell](../../config/hatch.md#shell) within the environment.

        This should either use
        [command_context](reference.md#hatch.env.plugin.interface.EnvironmentInterface.command_context)
        directly or provide the same guarantee.
        """
        with self.command_context():
            self.platform.exit_with_command([path, *args])

    def run_shell_command(self, command: str, **kwargs):
        """
        This should return the standard library's
        [subprocess.CompletedProcess](https://docs.python.org/3/library/subprocess.html#subprocess.CompletedProcess)
        and will always be called when the
        [command_context](reference.md#hatch.env.plugin.interface.EnvironmentInterface.command_context)
        is active, with the expectation of providing the same guarantee.
        """
        kwargs.setdefault('shell', True)
        return self.platform.run_command(command, **kwargs)

    @contextmanager
    def command_context(self):
        """
        A context manager that when active should make executed shell commands reflect any
        [environment variables](reference.md#hatch.env.plugin.interface.EnvironmentInterface.get_env_vars)
        the user defined either currently or at the time of
        [creation](reference.md#hatch.env.plugin.interface.EnvironmentInterface.create).

        For an example, open the default implementation below:
        """
        with self.get_env_vars():
            yield

    def resolve_commands(self, commands: list[str]):
        """
        This expands each command into one or more commands based on any
        [scripts](../../config/environment/overview.md#scripts) that the user defined.
        """
        for command in commands:
            yield from self.expand_command(command)

    def expand_command(self, command):
        possible_script, args, ignore_exit_code = parse_script_command(command)

        # Indicate undefined
        if not args:
            args = None

        with self.apply_context():
            if possible_script in self.scripts:
                for cmd in self.scripts[possible_script]:
                    yield self.metadata.context.format(cmd, args=args).strip()
            else:
                yield self.metadata.context.format(command, args=args).strip()

    def construct_build_command(
        self,
        *,
        directory=None,
        targets=(),
        hooks_only=False,
        no_hooks=False,
        clean=False,
        clean_hooks_after=False,
        clean_only=False,
    ):
        """
        This is the canonical way [`build`](../../cli/reference.md#hatch-build) command options are translated to
        a subprocess command issued to [builders](../builder/reference.md).
        """
        command = ['python', '-u', '-m', 'hatchling', 'build', '--app']

        if directory:
            command.extend(('--directory', directory))

        if targets:
            for target in targets:
                command.extend(('--target', target))

        if hooks_only:
            command.append('--hooks-only')

        if no_hooks:
            command.append('--no-hooks')

        if clean:
            command.append('--clean')

        if clean_hooks_after:
            command.append('--clean-hooks-after')

        if clean_only:
            command.append('--clean-only')

        return command

    def construct_pip_install_command(self, args: list[str]):
        """
        A convenience method for constructing a [`pip install`](https://pip.pypa.io/en/stable/cli/pip_install/)
        command with the given verbosity. The default verbosity is set to one less than Hatch's verbosity.
        """
        command = ['python', '-u', '-m', 'pip', 'install', '--disable-pip-version-check', '--no-python-version-warning']

        # Default to -1 verbosity
        add_verbosity_flag(command, self.verbosity, adjustment=-1)

        command.extend(args)
        return command

    def join_command_args(self, args: list[str]):
        """
        This is used by the [`run`](../../cli/reference.md#hatch-run) command to construct the root command string
        from the received arguments.
        """
        return self.platform.join_command_args(args)

    def apply_features(self, requirement: str):
        """
        A convenience method that applies any user defined [features](../../config/environment/overview.md#features)
        to the given requirement.
        """
        if self.features:
            features = ','.join(self.features)
            return f'{requirement}[{features}]'

        return requirement

    def check_compatibility(self):
        """
        This raises an exception if the environment is not compatible with the user's setup. The default behavior
        checks for [platform compatibility](../../config/environment/overview.md#supported-platforms)
        and any method override should keep this check.
        """
        if self.platforms and self.platform.name not in self.platforms:
            raise OSError('unsupported platform')

    def get_env_vars(self) -> EnvVars:
        """
        Returns a mapping of environment variables that should be available to the environment. The object can
        be used as a context manager to temporarily apply the environment variables to the current process.

        !!! note
            The environment variable `HATCH_ENV_ACTIVE` will always be set to the name of the environment.
        """
        return EnvVars(self.env_vars, self.env_include, self.env_exclude)

    def get_env_var_option(self, option: str) -> str:
        """
        Returns the value of the upper-cased environment variable `HATCH_ENV_TYPE_<PLUGIN_NAME>_<option>`.
        """
        return os.environ.get(f'{AppEnvVars.ENV_OPTION_PREFIX}{self.PLUGIN_NAME}_{option}'.upper(), '')

    def get_context(self):
        """
        Returns a subclass of
        [EnvironmentContextFormatter](../utilities.md#hatch.env.context.EnvironmentContextFormatter).
        """
        from hatch.env.context import EnvironmentContextFormatter

        return EnvironmentContextFormatter(self)

    @staticmethod
    def get_option_types() -> dict:
        """
        Returns a mapping of supported options to their respective types so that they can be used by
        [overrides](../../config/environment/advanced.md#option-overrides).
        """
        return {}

    @contextmanager
    def apply_context(self):
        with self.get_env_vars(), self.metadata.context.apply_context(self.context):
            yield

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.deactivate()


def expand_script_commands(env_name, script_name, commands, config, seen, active):
    if script_name in seen:
        return seen[script_name]
    elif script_name in active:
        active.append(script_name)
        raise ValueError(
            f'Circular expansion detected for field `tool.hatch.envs.{env_name}.scripts`: {" -> ".join(active)}'
        )

    active.append(script_name)

    expanded_commands = []

    for command in commands:
        possible_script, args, ignore_exit_code = parse_script_command(command)

        if possible_script in config:
            expanded_commands.extend(
                format_script_commands(
                    expand_script_commands(env_name, possible_script, config[possible_script], config, seen, active),
                    args,
                    ignore_exit_code,
                )
            )
        else:
            expanded_commands.append(command)

    seen[script_name] = expanded_commands
    active.pop()

    return expanded_commands
