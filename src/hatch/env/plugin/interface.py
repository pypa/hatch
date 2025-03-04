from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from functools import cached_property
from os.path import isabs
from typing import TYPE_CHECKING, Generator

from hatch.config.constants import AppEnvVars
from hatch.env.utils import add_verbosity_flag, get_env_var_option
from hatch.project.utils import format_script_commands, parse_script_command
from hatch.utils.structures import EnvVars

if TYPE_CHECKING:
    from collections.abc import Iterable

    from hatch.utils.fs import Path


class EnvironmentInterface(ABC):
    """
    Example usage:

    ```python tab="plugin.py"
        from hatch.env.plugin.interface import EnvironmentInterface


        class SpecialEnvironment(EnvironmentInterface):
            PLUGIN_NAME = 'special'
            ...
    ```

    ```python tab="hooks.py"
        from hatchling.plugin import hookimpl

        from .plugin import SpecialEnvironment


        @hookimpl
        def hatch_register_environment():
            return SpecialEnvironment
    ```
    """

    PLUGIN_NAME = ''
    """The name used for selection."""

    def __init__(
        self,
        root,
        metadata,
        name,
        config,
        matrix_variables,
        data_directory,
        isolated_data_directory,
        platform,
        verbosity,
        app,
    ):
        self.__root = root
        self.__metadata = metadata
        self.__name = name
        self.__config = config
        self.__matrix_variables = matrix_variables
        self.__data_directory = data_directory
        self.__isolated_data_directory = isolated_data_directory
        self.__platform = platform
        self.__verbosity = verbosity
        self.__app = app

    @property
    def matrix_variables(self):
        return self.__matrix_variables

    @property
    def app(self):
        """
        An instance of [Application](../utilities.md#hatchling.bridge.app.Application).
        """
        return self.__app

    @cached_property
    def context(self):
        return self.get_context()

    @property
    def verbosity(self):
        return self.__verbosity

    @property
    def root(self):
        """
        The root of the local project tree as a path-like object.
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
        The [directory](../../config/hatch.md#environments) this plugin should use for storage as a path-like object.
        If the user has not configured one then this will be the same as the
        [isolated data directory](reference.md#hatch.env.plugin.interface.EnvironmentInterface.isolated_data_directory).
        """
        return self.__data_directory

    @property
    def isolated_data_directory(self):
        """
        The default [directory](../../config/hatch.md#environments) reserved exclusively for this plugin as a path-like
        object.
        """
        return self.__isolated_data_directory

    @property
    def config(self) -> dict:
        """
        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>]
        ```
        """
        return self.__config

    @cached_property
    def project_root(self) -> str:
        """
        The root of the project tree as a string. If the environment is not running locally,
        this should be the remote path to the project.
        """
        return str(self.root)

    @cached_property
    def sep(self) -> str:
        """
        The character used to separate directories in paths. By default, this is `\\` on Windows and `/` otherwise.
        """
        return os.sep

    @cached_property
    def pathsep(self) -> str:
        """
        The character used to separate paths. By default, this is `;` on Windows and `:` otherwise.
        """
        return os.pathsep

    @cached_property
    def system_python(self):
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

        return system_python

    @cached_property
    def env_vars(self) -> dict:
        """
        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>.env-vars]
        ```
        """
        env_vars = self.config.get('env-vars', {})
        if not isinstance(env_vars, dict):
            message = f'Field `tool.hatch.envs.{self.name}.env-vars` must be a mapping'
            raise TypeError(message)

        for key, value in env_vars.items():
            if not isinstance(value, str):
                message = (
                    f'Environment variable `{key}` of field `tool.hatch.envs.{self.name}.env-vars` must be a string'
                )
                raise TypeError(message)

        new_env_vars = {}
        with self.metadata.context.apply_context(self.context):
            for key, value in env_vars.items():
                new_env_vars[key] = self.metadata.context.format(value)

        new_env_vars[AppEnvVars.ENV_ACTIVE] = self.name
        return new_env_vars

    @cached_property
    def env_include(self) -> list[str]:
        """
        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>]
        env-include = [...]
        ```
        """
        env_include = self.config.get('env-include', [])
        if not isinstance(env_include, list):
            message = f'Field `tool.hatch.envs.{self.name}.env-include` must be an array'
            raise TypeError(message)

        for i, pattern in enumerate(env_include, 1):
            if not isinstance(pattern, str):
                message = f'Pattern #{i} of field `tool.hatch.envs.{self.name}.env-include` must be a string'
                raise TypeError(message)

        return ['HATCH_BUILD_*', *env_include] if env_include else env_include

    @cached_property
    def env_exclude(self) -> list[str]:
        """
        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>]
        env-exclude = [...]
        ```
        """
        env_exclude = self.config.get('env-exclude', [])
        if not isinstance(env_exclude, list):
            message = f'Field `tool.hatch.envs.{self.name}.env-exclude` must be an array'
            raise TypeError(message)

        for i, pattern in enumerate(env_exclude, 1):
            if not isinstance(pattern, str):
                message = f'Pattern #{i} of field `tool.hatch.envs.{self.name}.env-exclude` must be a string'
                raise TypeError(message)

        return env_exclude

    @cached_property
    def environment_dependencies_complex(self):
        from packaging.requirements import InvalidRequirement, Requirement

        dependencies_complex = []
        with self.apply_context():
            for option in ('dependencies', 'extra-dependencies'):
                dependencies = self.config.get(option, [])
                if not isinstance(dependencies, list):
                    message = f'Field `tool.hatch.envs.{self.name}.{option}` must be an array'
                    raise TypeError(message)

                for i, entry in enumerate(dependencies, 1):
                    if not isinstance(entry, str):
                        message = f'Dependency #{i} of field `tool.hatch.envs.{self.name}.{option}` must be a string'
                        raise TypeError(message)

                    try:
                        dependencies_complex.append(Requirement(self.metadata.context.format(entry)))
                    except InvalidRequirement as e:
                        message = f'Dependency #{i} of field `tool.hatch.envs.{self.name}.{option}` is invalid: {e}'
                        raise ValueError(message) from None

        return dependencies_complex

    @cached_property
    def environment_dependencies(self) -> list[str]:
        """
        The list of all [environment dependencies](../../config/environment/overview.md#dependencies).
        """
        return [str(dependency) for dependency in self.environment_dependencies_complex]

    @cached_property
    def dependencies_complex(self):
        all_dependencies_complex = list(self.environment_dependencies_complex)
        if self.builder:
            all_dependencies_complex.extend(self.metadata.build.requires_complex)
            return all_dependencies_complex

        # Ensure these are checked last to speed up initial environment creation since
        # they will already be installed along with the project
        if (not self.skip_install and self.dev_mode) or self.features or self.dependency_groups:
            from hatch.utils.dep import get_complex_dependencies, get_complex_dependency_group, get_complex_features

            dependencies, optional_dependencies = self.app.project.get_dependencies()
            dependencies_complex = get_complex_dependencies(dependencies)
            optional_dependencies_complex = get_complex_features(optional_dependencies)

            if not self.skip_install and self.dev_mode:
                all_dependencies_complex.extend(dependencies_complex.values())

            for feature in self.features:
                if feature not in optional_dependencies_complex:
                    message = (
                        f'Feature `{feature}` of field `tool.hatch.envs.{self.name}.features` is not '
                        f'defined in the dynamic field `project.optional-dependencies`'
                    )
                    raise ValueError(message)

                all_dependencies_complex.extend(optional_dependencies_complex[feature].values())

            for dependency_group in self.dependency_groups:
                all_dependencies_complex.extend(
                    get_complex_dependency_group(self.app.project.dependency_groups, dependency_group)
                )

        return all_dependencies_complex

    @cached_property
    def dependencies(self) -> list[str]:
        """
        The list of all [project dependencies](../../config/metadata.md#dependencies) (if
        [installed](../../config/environment/overview.md#skip-install) and in
        [dev mode](../../config/environment/overview.md#dev-mode)), selected
        [optional dependencies](../../config/environment/overview.md#features), and
        [environment dependencies](../../config/environment/overview.md#dependencies).
        """
        return [str(dependency) for dependency in self.dependencies_complex]

    @cached_property
    def platforms(self) -> list[str]:
        """
        All names are stored as their lower-cased version.

        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>]
        platforms = [...]
        ```
        """
        platforms = self.config.get('platforms', [])
        if not isinstance(platforms, list):
            message = f'Field `tool.hatch.envs.{self.name}.platforms` must be an array'
            raise TypeError(message)

        for i, command in enumerate(platforms, 1):
            if not isinstance(command, str):
                message = f'Platform #{i} of field `tool.hatch.envs.{self.name}.platforms` must be a string'
                raise TypeError(message)

        return [platform.lower() for platform in platforms]

    @cached_property
    def skip_install(self) -> bool:
        """
        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>]
        skip-install = ...
        ```
        """
        skip_install = self.config.get('skip-install', not self.metadata.has_project_file())
        if not isinstance(skip_install, bool):
            message = f'Field `tool.hatch.envs.{self.name}.skip-install` must be a boolean'
            raise TypeError(message)

        return skip_install

    @cached_property
    def dev_mode(self) -> bool:
        """
        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>]
        dev-mode = ...
        ```
        """
        dev_mode = self.config.get('dev-mode', True)
        if not isinstance(dev_mode, bool):
            message = f'Field `tool.hatch.envs.{self.name}.dev-mode` must be a boolean'
            raise TypeError(message)

        return dev_mode

    @cached_property
    def builder(self) -> bool:
        """
        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>]
        builder = ...
        ```
        """
        builder = self.config.get('builder', False)
        if not isinstance(builder, bool):
            message = f'Field `tool.hatch.envs.{self.name}.builder` must be a boolean'
            raise TypeError(message)

        return builder

    @cached_property
    def features(self):
        from hatchling.metadata.utils import normalize_project_name

        features = self.config.get('features', [])
        if not isinstance(features, list):
            message = f'Field `tool.hatch.envs.{self.name}.features` must be an array of strings'
            raise TypeError(message)

        all_features = set()
        for i, feature in enumerate(features, 1):
            if not isinstance(feature, str):
                message = f'Feature #{i} of field `tool.hatch.envs.{self.name}.features` must be a string'
                raise TypeError(message)

            if not feature:
                message = f'Feature #{i} of field `tool.hatch.envs.{self.name}.features` cannot be an empty string'
                raise ValueError(message)

            normalized_feature = (
                feature if self.metadata.hatch.metadata.allow_ambiguous_features else normalize_project_name(feature)
            )
            if (
                not self.metadata.hatch.metadata.hook_config
                and normalized_feature not in self.metadata.core.optional_dependencies
            ):
                message = (
                    f'Feature `{normalized_feature}` of field `tool.hatch.envs.{self.name}.features` is not '
                    f'defined in field `project.optional-dependencies`'
                )
                raise ValueError(message)

            all_features.add(normalized_feature)

        return sorted(all_features)

    @cached_property
    def dependency_groups(self):
        from hatchling.metadata.utils import normalize_project_name

        dependency_groups = self.config.get('dependency-groups', [])
        if not isinstance(dependency_groups, list):
            message = f'Field `tool.hatch.envs.{self.name}.dependency-groups` must be an array of strings'
            raise TypeError(message)

        all_dependency_groups = set()
        for i, dependency_group in enumerate(dependency_groups, 1):
            if not isinstance(dependency_group, str):
                message = (
                    f'Dependency Group #{i} of field `tool.hatch.envs.{self.name}.dependency-groups` must be a string'
                )
                raise TypeError(message)

            if not dependency_group:
                message = f'Dependency Group #{i} of field `tool.hatch.envs.{self.name}.dependency-groups` cannot be an empty string'
                raise ValueError(message)

            normalized_dependency_group = normalize_project_name(dependency_group)
            if (
                not self.metadata.hatch.metadata.hook_config
                and normalized_dependency_group not in self.app.project.dependency_groups
            ):
                message = (
                    f'Dependency Group `{normalized_dependency_group}` of field `tool.hatch.envs.{self.name}.dependency-groups` is not '
                    f'defined in field `dependency-groups`'
                )
                raise ValueError(message)

            all_dependency_groups.add(normalized_dependency_group)

        return sorted(all_dependency_groups)

    @cached_property
    def description(self) -> str:
        """
        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>]
        description = ...
        ```
        """
        description = self.config.get('description', '')
        if not isinstance(description, str):
            message = f'Field `tool.hatch.envs.{self.name}.description` must be a string'
            raise TypeError(message)

        return description

    @cached_property
    def scripts(self):
        config = {}

        # Extra scripts should come first to give less precedence
        for field in ('extra-scripts', 'scripts'):
            script_config = self.config.get(field, {})
            if not isinstance(script_config, dict):
                message = f'Field `tool.hatch.envs.{self.name}.{field}` must be a table'
                raise TypeError(message)

            for name, data in script_config.items():
                if ' ' in name:
                    message = (
                        f'Script name `{name}` in field `tool.hatch.envs.{self.name}.{field}` '
                        f'must not contain spaces'
                    )
                    raise ValueError(message)

                commands = []

                if isinstance(data, str):
                    commands.append(data)
                elif isinstance(data, list):
                    for i, command in enumerate(data, 1):
                        if not isinstance(command, str):
                            message = (
                                f'Command #{i} in field `tool.hatch.envs.{self.name}.{field}.{name}` '
                                f'must be a string'
                            )
                            raise TypeError(message)

                        commands.append(command)
                else:
                    message = (
                        f'Field `tool.hatch.envs.{self.name}.{field}.{name}` must be '
                        f'a string or an array of strings'
                    )
                    raise TypeError(message)

                config[name] = commands

        seen = {}
        active = []
        for script_name, commands in config.items():
            commands[:] = expand_script_commands(self.name, script_name, commands, config, seen, active)

        return config

    @cached_property
    def pre_install_commands(self):
        pre_install_commands = self.config.get('pre-install-commands', [])
        if not isinstance(pre_install_commands, list):
            message = f'Field `tool.hatch.envs.{self.name}.pre-install-commands` must be an array'
            raise TypeError(message)

        for i, command in enumerate(pre_install_commands, 1):
            if not isinstance(command, str):
                message = f'Command #{i} of field `tool.hatch.envs.{self.name}.pre-install-commands` must be a string'
                raise TypeError(message)

        return list(pre_install_commands)

    @cached_property
    def post_install_commands(self):
        post_install_commands = self.config.get('post-install-commands', [])
        if not isinstance(post_install_commands, list):
            message = f'Field `tool.hatch.envs.{self.name}.post-install-commands` must be an array'
            raise TypeError(message)

        for i, command in enumerate(post_install_commands, 1):
            if not isinstance(command, str):
                message = f'Command #{i} of field `tool.hatch.envs.{self.name}.post-install-commands` must be a string'
                raise TypeError(message)

        return list(post_install_commands)

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

        This should return information about how to locate the environment or represent its ID in
        some way. Additionally, this is expected to return something even if the environment is
        [incompatible](reference.md#hatch.env.plugin.interface.EnvironmentInterface.check_compatibility).
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

    def dependency_hash(self):
        """
        This should return a hash of the environment's
        [dependencies](reference.md#hatch.env.plugin.interface.EnvironmentInterface.dependencies)
        and any other data that is handled by the
        [sync_dependencies](reference.md#hatch.env.plugin.interface.EnvironmentInterface.sync_dependencies)
        and
        [dependencies_in_sync](reference.md#hatch.env.plugin.interface.EnvironmentInterface.dependencies_in_sync)
        methods.
        """
        from hatch.utils.dep import hash_dependencies

        return hash_dependencies(self.dependencies_complex)

    @contextmanager
    def app_status_creation(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        with self.app.status(f'Creating environment: {self.name}'):
            yield

    @contextmanager
    def app_status_pre_installation(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        with self.app.status('Running pre-installation commands'):
            yield

    @contextmanager
    def app_status_post_installation(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        with self.app.status('Running post-installation commands'):
            yield

    @contextmanager
    def app_status_project_installation(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        if self.dev_mode:
            with self.app.status('Installing project in development mode'):
                yield
        else:
            with self.app.status('Installing project'):
                yield

    @contextmanager
    def app_status_dependency_state_check(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        if not self.skip_install and (
            'dependencies' in self.metadata.dynamic or 'optional-dependencies' in self.metadata.dynamic
        ):
            with self.app.status('Polling dependency state'):
                yield
        else:
            yield

    @contextmanager
    def app_status_dependency_installation_check(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        with self.app.status('Checking dependencies'):
            yield

    @contextmanager
    def app_status_dependency_synchronization(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        with self.app.status('Syncing dependencies'):
            yield

    @contextmanager
    def fs_context(self) -> Generator[FileSystemContext, None, None]:
        """
        A context manager that must yield a subclass of
        [FileSystemContext](../utilities.md#hatch.env.plugin.interface.FileSystemContext).
        """
        from hatch.utils.fs import temp_directory

        with temp_directory() as temp_dir:
            yield FileSystemContext(self, local_path=temp_dir, env_path=str(temp_dir))

    def enter_shell(
        self,
        name: str,  # noqa: ARG002
        path: str,
        args: Iterable[str],
    ):
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
        possible_script, args, _ignore_exit_code = parse_script_command(command)

        # Indicate undefined
        if not args:
            args = None

        with self.apply_context():
            if possible_script in self.scripts:
                if args is not None:
                    args = self.metadata.context.format(args)

                for cmd in self.scripts[possible_script]:
                    yield self.metadata.context.format(cmd, args=args).strip()
            else:
                yield self.metadata.context.format(command, args=args).strip()

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

        This check is never performed if the environment has been
        [created](reference.md#hatch.env.plugin.interface.EnvironmentInterface.create).
        """
        if self.platforms and self.platform.name not in self.platforms:
            message = 'unsupported platform'
            raise OSError(message)

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
        return get_env_var_option(plugin_name=self.PLUGIN_NAME, option=option)

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


class FileSystemContext:
    """
    This class represents a synchronized path between the local file system and a potentially remote environment.
    """

    def __init__(self, env: EnvironmentInterface, *, local_path: Path, env_path: str):
        self.__env = env
        self.__local_path = local_path
        self.__env_path = env_path

    @property
    def env(self) -> EnvironmentInterface:
        """
        Returns the environment to which this context belongs.
        """
        return self.__env

    @property
    def local_path(self) -> Path:
        """
        Returns the local path to which this context refers as a path-like object.
        """
        return self.__local_path

    @property
    def env_path(self) -> str:
        """
        Returns the environment path to which this context refers as a string. The environment
        may not be on the local file system.
        """
        return self.__env_path

    def join(self, relative_path: str) -> FileSystemContext:
        """
        Returns a new instance of this class with the given relative path appended to the local and
        environment paths.

        This method should not need overwriting.
        """
        local_path = self.local_path / relative_path
        env_path = f'{self.env_path}{self.__env.sep.join(["", *os.path.normpath(relative_path).split(os.sep)])}'
        return FileSystemContext(self.__env, local_path=local_path, env_path=env_path)

    def sync_env(self):
        """
        Synchronizes the [environment path](utilities.md#hatch.env.plugin.interface.FileSystemContext.env_path)
        with the [local path](utilities.md#hatch.env.plugin.interface.FileSystemContext.local_path) as the source.
        """

    def sync_local(self):
        """
        Synchronizes the [local path](utilities.md#hatch.env.plugin.interface.FileSystemContext.local_path) as the
        source with the [environment path](utilities.md#hatch.env.plugin.interface.FileSystemContext.env_path) as
        the source.
        """


def expand_script_commands(env_name, script_name, commands, config, seen, active):
    if script_name in seen:
        return seen[script_name]

    if script_name in active:
        active.append(script_name)

        message = f'Circular expansion detected for field `tool.hatch.envs.{env_name}.scripts`: {" -> ".join(active)}'
        raise ValueError(message)

    active.append(script_name)

    expanded_commands = []

    for command in commands:
        possible_script, args, ignore_exit_code = parse_script_command(command)

        if possible_script in config:
            expanded_commands.extend(
                format_script_commands(
                    commands=expand_script_commands(
                        env_name, possible_script, config[possible_script], config, seen, active
                    ),
                    args=args,
                    ignore_exit_code=ignore_exit_code,
                )
            )
        else:
            expanded_commands.append(command)

    seen[script_name] = expanded_commands
    active.pop()

    return expanded_commands
