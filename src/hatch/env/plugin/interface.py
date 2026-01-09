from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from functools import cached_property
from os.path import isabs
from typing import TYPE_CHECKING, Any

from hatch.config.constants import AppEnvVars
from hatch.env.utils import add_verbosity_flag, get_env_var_option
from hatch.project.utils import format_script_commands, parse_script_command
from hatch.utils.structures import EnvVars

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from hatch.dep.core import Dependency
    from hatch.project.core import Project
    from hatch.utils.fs import Path


class EnvironmentInterface(ABC):
    """
    Example usage:

    ```python tab="plugin.py"
    from hatch.env.plugin.interface import EnvironmentInterface


    class SpecialEnvironment(EnvironmentInterface):
        PLUGIN_NAME = "special"
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

    PLUGIN_NAME = ""
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

        self.additional_dependencies = []

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
    def system_python(self) -> str:
        system_python = os.environ.get(AppEnvVars.PYTHON)
        if system_python == "self":
            system_python = sys.executable

        system_python = (
            system_python
            or self.platform.modules.shutil.which("python")
            or self.platform.modules.shutil.which("python3")
            or sys.executable
        )
        if not isabs(system_python):
            system_python = self.platform.modules.shutil.which(system_python)

        return system_python

    @cached_property
    def env_vars(self) -> dict[str, str]:
        """
        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>.env-vars]
        ```
        """
        env_vars = self.config.get("env-vars", {})
        if not isinstance(env_vars, dict):
            message = f"Field `tool.hatch.envs.{self.name}.env-vars` must be a mapping"
            raise TypeError(message)

        for key, value in env_vars.items():
            if not isinstance(value, str):
                message = (
                    f"Environment variable `{key}` of field `tool.hatch.envs.{self.name}.env-vars` must be a string"
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
        env_include = self.config.get("env-include", [])
        if not isinstance(env_include, list):
            message = f"Field `tool.hatch.envs.{self.name}.env-include` must be an array"
            raise TypeError(message)

        for i, pattern in enumerate(env_include, 1):
            if not isinstance(pattern, str):
                message = f"Pattern #{i} of field `tool.hatch.envs.{self.name}.env-include` must be a string"
                raise TypeError(message)

        return ["HATCH_BUILD_*", *env_include] if env_include else env_include

    @cached_property
    def env_exclude(self) -> list[str]:
        """
        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>]
        env-exclude = [...]
        ```
        """
        env_exclude = self.config.get("env-exclude", [])
        if not isinstance(env_exclude, list):
            message = f"Field `tool.hatch.envs.{self.name}.env-exclude` must be an array"
            raise TypeError(message)

        for i, pattern in enumerate(env_exclude, 1):
            if not isinstance(pattern, str):
                message = f"Pattern #{i} of field `tool.hatch.envs.{self.name}.env-exclude` must be a string"
                raise TypeError(message)

        return env_exclude

    @cached_property
    def environment_dependencies_complex(self) -> list[Dependency]:
        from hatch.dep.core import Dependency, InvalidDependencyError

        dependencies_complex: list[Dependency] = []
        with self.apply_context():
            for option in ("dependencies", "extra-dependencies"):
                dependencies = self.config.get(option, [])
                if not isinstance(dependencies, list):
                    message = f"Field `tool.hatch.envs.{self.name}.{option}` must be an array"
                    raise TypeError(message)

                for i, entry in enumerate(dependencies, 1):
                    if not isinstance(entry, str):
                        message = f"Dependency #{i} of field `tool.hatch.envs.{self.name}.{option}` must be a string"
                        raise TypeError(message)

                    try:
                        dependencies_complex.append(Dependency(self.metadata.context.format(entry)))
                    except InvalidDependencyError as e:
                        message = f"Dependency #{i} of field `tool.hatch.envs.{self.name}.{option}` is invalid: {e}"
                        raise ValueError(message) from None

        return dependencies_complex

    @cached_property
    def environment_dependencies(self) -> list[str]:
        """
        The list of all [environment dependencies](../../config/environment/overview.md#dependencies).
        """
        return [str(dependency) for dependency in self.environment_dependencies_complex]

    @cached_property
    def project_dependencies_complex(self) -> list[Dependency]:
        workspace_dependencies = self.workspace.get_dependencies()
        if self.skip_install and not self.features and not self.dependency_groups and not workspace_dependencies:
            return []

        from hatch.dep.core import Dependency
        from hatch.utils.dep import get_complex_dependencies, get_complex_dependency_group, get_complex_features

        all_dependencies_complex = list(map(Dependency, workspace_dependencies))
        dependencies, optional_dependencies = self.app.project.get_dependencies()

        # Format dependencies with context before creating Dependency objects
        with self.apply_context():
            formatted_dependencies = [self.metadata.context.format(dep) for dep in dependencies]
            formatted_optional_dependencies = {
                feature: [self.metadata.context.format(dep) for dep in deps]
                for feature, deps in optional_dependencies.items()
            }

        dependencies_complex = get_complex_dependencies(formatted_dependencies)
        optional_dependencies_complex = get_complex_features(formatted_optional_dependencies)

        if not self.skip_install:
            all_dependencies_complex.extend(dependencies_complex.values())

        for feature in self.features:
            if feature not in optional_dependencies_complex:
                message = (
                    f"Feature `{feature}` of field `tool.hatch.envs.{self.name}.features` is not "
                    f"defined in the dynamic field `project.optional-dependencies`"
                )
                raise ValueError(message)

            all_dependencies_complex.extend([
                dep if isinstance(dep, Dependency) else Dependency(str(dep))
                for dep in optional_dependencies_complex[feature]
            ])

        for dependency_group in self.dependency_groups:
            all_dependencies_complex.extend(
                get_complex_dependency_group(self.app.project.dependency_groups, dependency_group)
            )

        return all_dependencies_complex

    @cached_property
    def project_dependencies(self) -> list[str]:
        """
        The list of all [project dependencies](../../config/metadata.md#dependencies) (if
        [installed](../../config/environment/overview.md#skip-install)), selected
        [optional dependencies](../../config/environment/overview.md#features), and
        workspace dependencies.
        """
        return [str(dependency) for dependency in self.project_dependencies_complex]

    @cached_property
    def local_dependencies_complex(self) -> list[Dependency]:
        from hatch.dep.core import Dependency

        local_dependencies_complex = []
        if not self.skip_install:
            local_dependencies_complex.append(
                Dependency(f"{self.metadata.name} @ {self.root.as_uri()}", editable=self.dev_mode)
            )
        if self.workspace.members:
            local_dependencies_complex.extend(
                Dependency(f"{member.project.metadata.name} @ {member.project.location.as_uri()}", editable=True)
                for member in self.workspace.members
            )

        return local_dependencies_complex

    @cached_property
    def dependencies_complex(self) -> list[Dependency]:
        from hatch.dep.core import Dependency

        all_dependencies_complex = list(self.environment_dependencies_complex)

        # Convert additional_dependencies to Dependency objects
        for dep in self.additional_dependencies:
            if isinstance(dep, Dependency):
                all_dependencies_complex.append(dep)
            else:
                all_dependencies_complex.append(Dependency(str(dep)))

        if self.dependency_groups and not self.skip_install:
            from hatch.utils.dep import get_complex_dependency_group

            for dependency_group in self.dependency_groups:
                all_dependencies_complex.extend(
                    get_complex_dependency_group(self.app.project.dependency_groups, dependency_group)
                )

        if self.builder:
            from hatch.project.constants import BuildEnvVars

            # Convert build requirements to Dependency objects
            for req in self.metadata.build.requires_complex:
                if isinstance(req, Dependency):
                    all_dependencies_complex.append(req)
                else:
                    all_dependencies_complex.append(Dependency(str(req)))

            for target in os.environ.get(BuildEnvVars.REQUESTED_TARGETS, "").split():
                target_config = self.app.project.config.build.target(target)
                all_dependencies_complex.extend(map(Dependency, target_config.dependencies))

            return all_dependencies_complex

        # Ensure these are checked last to speed up initial environment creation since
        # they will already be installed along with the project
        if self.dev_mode or self.features or self.dependency_groups:
            all_dependencies_complex.extend(self.project_dependencies_complex)

        return all_dependencies_complex

    @cached_property
    def dependencies(self) -> list[str]:
        """
        The list of all
        [project dependencies](reference.md#hatch.env.plugin.interface.EnvironmentInterface.project_dependencies)
        (if in [dev mode](../../config/environment/overview.md#dev-mode)) and
        [environment dependencies](../../config/environment/overview.md#dependencies).
        """
        return [str(dependency) for dependency in self.dependencies_complex]

    @cached_property
    def all_dependencies_complex(self) -> list[Dependency]:
        from hatch.dep.core import Dependency

        local_deps = list(self.local_dependencies_complex)
        workspace_names = {dep.name.lower() for dep in local_deps}

        filtered_deps: list[Dependency] = []
        for dep in self.dependencies_complex:
            dep_obj = dep if isinstance(dep, Dependency) else Dependency(str(dep))

            if dep_obj.name.lower() in workspace_names and dep_obj.extras:
                # Only expand if we have static optional dependencies to avoid recursion
                if not self.metadata.hatch.metadata.hook_config:
                    optional_dependencies = self.metadata.core.optional_dependencies
                    for extra in dep_obj.extras:
                        if extra in optional_dependencies:
                            filtered_deps.extend(Dependency(d) for d in optional_dependencies[extra])
            elif dep_obj.name.lower() not in workspace_names:
                filtered_deps.append(dep_obj)

        return local_deps + filtered_deps

    @cached_property
    def all_dependencies(self) -> list[str]:
        return [str(dependency) for dependency in self.all_dependencies_complex]

    @cached_property
    def platforms(self) -> list[str]:
        """
        All names are stored as their lower-cased version.

        ```toml config-example
        [tool.hatch.envs.<ENV_NAME>]
        platforms = [...]
        ```
        """
        platforms = self.config.get("platforms", [])
        if not isinstance(platforms, list):
            message = f"Field `tool.hatch.envs.{self.name}.platforms` must be an array"
            raise TypeError(message)

        for i, command in enumerate(platforms, 1):
            if not isinstance(command, str):
                message = f"Platform #{i} of field `tool.hatch.envs.{self.name}.platforms` must be a string"
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
        skip_install = self.config.get("skip-install", not self.metadata.has_project_file())
        if not isinstance(skip_install, bool):
            message = f"Field `tool.hatch.envs.{self.name}.skip-install` must be a boolean"
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
        dev_mode = self.config.get("dev-mode", True)
        if not isinstance(dev_mode, bool):
            message = f"Field `tool.hatch.envs.{self.name}.dev-mode` must be a boolean"
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
        builder = self.config.get("builder", False)
        if not isinstance(builder, bool):
            message = f"Field `tool.hatch.envs.{self.name}.builder` must be a boolean"
            raise TypeError(message)

        return builder

    @cached_property
    def features(self):
        from hatch.utils.metadata import normalize_project_name

        features = self.config.get("features", [])
        if not isinstance(features, list):
            message = f"Field `tool.hatch.envs.{self.name}.features` must be an array of strings"
            raise TypeError(message)

        all_features = set()
        for i, feature in enumerate(features, 1):
            if not isinstance(feature, str):
                message = f"Feature #{i} of field `tool.hatch.envs.{self.name}.features` must be a string"
                raise TypeError(message)

            if not feature:
                message = f"Feature #{i} of field `tool.hatch.envs.{self.name}.features` cannot be an empty string"
                raise ValueError(message)

            normalized_feature = (
                feature if self.metadata.hatch.metadata.allow_ambiguous_features else normalize_project_name(feature)
            )
            if (
                not self.metadata.hatch.metadata.hook_config
                and normalized_feature not in self.metadata.core.optional_dependencies
            ):
                message = (
                    f"Feature `{normalized_feature}` of field `tool.hatch.envs.{self.name}.features` is not "
                    f"defined in field `project.optional-dependencies`"
                )
                raise ValueError(message)

            all_features.add(normalized_feature)

        return sorted(all_features)

    @cached_property
    def dependency_groups(self):
        from hatch.utils.metadata import normalize_project_name

        dependency_groups = self.config.get("dependency-groups", [])
        if not isinstance(dependency_groups, list):
            message = f"Field `tool.hatch.envs.{self.name}.dependency-groups` must be an array of strings"
            raise TypeError(message)

        all_dependency_groups = set()
        for i, dependency_group in enumerate(dependency_groups, 1):
            if not isinstance(dependency_group, str):
                message = (
                    f"Dependency Group #{i} of field `tool.hatch.envs.{self.name}.dependency-groups` must be a string"
                )
                raise TypeError(message)

            if not dependency_group:
                message = f"Dependency Group #{i} of field `tool.hatch.envs.{self.name}.dependency-groups` cannot be an empty string"
                raise ValueError(message)

            normalized_dependency_group = normalize_project_name(dependency_group)
            if (
                not self.metadata.hatch.metadata.hook_config
                and normalized_dependency_group not in self.app.project.dependency_groups
            ):
                message = (
                    f"Dependency Group `{normalized_dependency_group}` of field `tool.hatch.envs.{self.name}.dependency-groups` is not "
                    f"defined in field `dependency-groups`"
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
        description = self.config.get("description", "")
        if not isinstance(description, str):
            message = f"Field `tool.hatch.envs.{self.name}.description` must be a string"
            raise TypeError(message)

        return description

    @cached_property
    def scripts(self):
        config = {}

        # Extra scripts should come first to give less precedence
        for field in ("extra-scripts", "scripts"):
            script_config = self.config.get(field, {})
            if not isinstance(script_config, dict):
                message = f"Field `tool.hatch.envs.{self.name}.{field}` must be a table"
                raise TypeError(message)

            for name, data in script_config.items():
                if " " in name:
                    message = (
                        f"Script name `{name}` in field `tool.hatch.envs.{self.name}.{field}` must not contain spaces"
                    )
                    raise ValueError(message)

                commands = []

                if isinstance(data, str):
                    commands.append(data)
                elif isinstance(data, list):
                    for i, command in enumerate(data, 1):
                        if not isinstance(command, str):
                            message = (
                                f"Command #{i} in field `tool.hatch.envs.{self.name}.{field}.{name}` must be a string"
                            )
                            raise TypeError(message)

                        commands.append(command)
                else:
                    message = (
                        f"Field `tool.hatch.envs.{self.name}.{field}.{name}` must be a string or an array of strings"
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
        pre_install_commands = self.config.get("pre-install-commands", [])
        if not isinstance(pre_install_commands, list):
            message = f"Field `tool.hatch.envs.{self.name}.pre-install-commands` must be an array"
            raise TypeError(message)

        for i, command in enumerate(pre_install_commands, 1):
            if not isinstance(command, str):
                message = f"Command #{i} of field `tool.hatch.envs.{self.name}.pre-install-commands` must be a string"
                raise TypeError(message)

        return list(pre_install_commands)

    @cached_property
    def post_install_commands(self):
        post_install_commands = self.config.get("post-install-commands", [])
        if not isinstance(post_install_commands, list):
            message = f"Field `tool.hatch.envs.{self.name}.post-install-commands` must be an array"
            raise TypeError(message)

        for i, command in enumerate(post_install_commands, 1):
            if not isinstance(command, str):
                message = f"Command #{i} of field `tool.hatch.envs.{self.name}.post-install-commands` must be a string"
                raise TypeError(message)

        return list(post_install_commands)

    @cached_property
    def workspace(self) -> Workspace:
        env_config = self.config.get("workspace", {})
        if not isinstance(env_config, dict):
            message = f"Field `tool.hatch.envs.{self.name}.workspace` must be a table"
            raise TypeError(message)

        return Workspace(self, env_config)

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

        return hash_dependencies(self.all_dependencies_complex)

    @contextmanager
    def app_status_creation(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        with self.app.status(f"Creating environment: {self.name}"):
            yield

    @contextmanager
    def app_status_pre_installation(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        with self.app.status("Running pre-installation commands"):
            yield

    @contextmanager
    def app_status_post_installation(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        with self.app.status("Running post-installation commands"):
            yield

    @contextmanager
    def app_status_project_installation(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        if self.dev_mode:
            with self.app.status("Installing project in development mode"):
                yield
        else:
            with self.app.status("Installing project"):
                yield

    @contextmanager
    def app_status_dependency_state_check(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        if not self.skip_install and (
            "dependencies" in self.metadata.dynamic or "optional-dependencies" in self.metadata.dynamic
        ):
            with self.app.status("Polling dependency state"):
                yield
        else:
            yield

    @contextmanager
    def app_status_dependency_installation_check(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        with self.app.status("Checking dependencies"):
            yield

    @contextmanager
    def app_status_dependency_synchronization(self):
        """
        See the [life cycle of environments](reference.md#life-cycle).
        """
        with self.app.status("Syncing dependencies"):
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
        kwargs.setdefault("shell", True)
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
        command = ["python", "-u", "-m", "pip", "install", "--disable-pip-version-check"]

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
            features = ",".join(self.features)
            return f"{requirement}[{features}]"

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
            message = "unsupported platform"
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
        env_path = f"{self.env_path}{self.__env.sep.join(['', *os.path.normpath(relative_path).split(os.sep)])}"
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


class Workspace:
    def __init__(self, env: EnvironmentInterface, config: dict[str, Any]):
        self.env = env
        self.config = config

    @cached_property
    def parallel(self) -> bool:
        parallel = self.config.get("parallel", True)
        if not isinstance(parallel, bool):
            message = f"Field `tool.hatch.envs.{self.env.name}.workspace.parallel` must be a boolean"
            raise TypeError(message)

        return parallel

    def get_dependencies(self) -> list[str]:
        static_members: list[WorkspaceMember] = []
        dynamic_members: list[WorkspaceMember] = []
        for member in self.members:
            if member.has_static_dependencies:
                static_members.append(member)
            else:
                dynamic_members.append(member)

        all_dependencies = []
        for member in static_members:
            dependencies, features = member.get_dependencies()
            all_dependencies.extend(dependencies)
            for feature in member.features:
                all_dependencies.extend(features.get(feature, []))

        if self.parallel:
            from concurrent.futures import ThreadPoolExecutor

            def get_member_deps(member):
                with self.env.app.status(f"Checking workspace member: {member.name}"):
                    dependencies, features = member.get_dependencies()
                    deps = list(dependencies)
                    for feature in member.features:
                        deps.extend(features.get(feature, []))
                    return deps

            with ThreadPoolExecutor() as executor:
                results = executor.map(get_member_deps, dynamic_members)
                for deps in results:
                    all_dependencies.extend(deps)
        else:
            for member in dynamic_members:
                with self.env.app.status(f"Checking workspace member: {member.name}"):
                    dependencies, features = member.get_dependencies()
                    all_dependencies.extend(dependencies)
                    for feature in member.features:
                        all_dependencies.extend(features.get(feature, []))

        return all_dependencies

    @cached_property
    def members(self) -> list[WorkspaceMember]:
        import fnmatch

        from hatch.project.core import Project
        from hatch.utils.fs import Path
        from hatch.utils.metadata import normalize_project_name

        raw_members = self.config.get("members", [])
        if not isinstance(raw_members, list):
            message = f"Field `tool.hatch.envs.{self.env.name}.workspace.members` must be an array"
            raise TypeError(message)

        # Get exclude patterns
        exclude_patterns = self.config.get("exclude", [])
        if not isinstance(exclude_patterns, list):
            message = f"Field `tool.hatch.envs.{self.env.name}.workspace.exclude` must be an array"
            raise TypeError(message)

        # First normalize configuration with context expansion
        member_data: list[dict[str, Any]] = []
        with self.env.apply_context():
            for i, data in enumerate(raw_members, 1):
                if isinstance(data, str):
                    expanded_path = self.env.metadata.context.format(data)
                    member_data.append({"path": expanded_path, "features": ()})
                elif isinstance(data, dict):
                    if "path" not in data:
                        message = (
                            f"Member #{i} of field `tool.hatch.envs.{self.env.name}.workspace.members` must define "
                            f"a `path` key"
                        )
                        raise TypeError(message)

                    path = data["path"]
                    if not isinstance(path, str):
                        message = (
                            f"Option `path` of member #{i} of field `tool.hatch.envs.{self.env.name}.workspace.members` "
                            f"must be a string"
                        )
                        raise TypeError(message)

                    if not path:
                        message = (
                            f"Option `path` of member #{i} of field `tool.hatch.envs.{self.env.name}.workspace.members` "
                            f"cannot be an empty string"
                        )
                        raise ValueError(message)

                    expanded_path = self.env.metadata.context.format(path)

                    features = data.get("features", [])
                    if not isinstance(features, list):
                        message = (
                            f"Option `features` of member #{i} of field `tool.hatch.envs.{self.env.name}.workspace."
                            f"members` must be an array of strings"
                        )
                        raise TypeError(message)

                    all_features: set[str] = set()
                    for j, feature in enumerate(features, 1):
                        if not isinstance(feature, str):
                            message = (
                                f"Feature #{j} of option `features` of member #{i} of field "
                                f"`tool.hatch.envs.{self.env.name}.workspace.members` must be a string"
                            )
                            raise TypeError(message)

                        if not feature:
                            message = (
                                f"Feature #{j} of option `features` of member #{i} of field "
                                f"`tool.hatch.envs.{self.env.name}.workspace.members` cannot be an empty string"
                            )
                            raise ValueError(message)

                        normalized_feature = normalize_project_name(feature)
                        if normalized_feature in all_features:
                            message = (
                                f"Feature #{j} of option `features` of member #{i} of field "
                                f"`tool.hatch.envs.{self.env.name}.workspace.members` is a duplicate"
                            )
                            raise ValueError(message)

                        all_features.add(normalized_feature)

                    member_data.append({"path": expanded_path, "features": tuple(sorted(all_features))})
                else:
                    message = (
                        f"Member #{i} of field `tool.hatch.envs.{self.env.name}.workspace.members` must be "
                        f"a string or an inline table"
                    )
                    raise TypeError(message)

        root = str(self.env.root)
        member_paths: dict[str, WorkspaceMember] = {}
        for data in member_data:
            # Given root R and member spec M, we need to find:
            #
            # 1. The absolute path AP of R/M
            # 2. The shared prefix SP of R and AP
            # 3. The relative path RP of M from AP
            #
            # For example, if:
            #
            # R = /foo/bar/baz
            # M = ../dir/pkg-*
            #
            # Then:
            #
            # AP = /foo/bar/dir/pkg-*
            # SP = /foo/bar
            # RP = dir/pkg-*
            path_spec = data["path"]
            normalized_path = os.path.normpath(os.path.join(root, path_spec))
            absolute_path = os.path.abspath(normalized_path)
            shared_prefix = os.path.commonprefix([root, absolute_path])
            relative_path = os.path.relpath(absolute_path, shared_prefix)

            # Now we have the necessary information to perform an optimized glob search for members
            members_found = False
            for member_path in find_members(shared_prefix, relative_path.split(os.sep)):
                # Check if member should be excluded
                relative_member_path = os.path.relpath(member_path, shared_prefix)
                should_exclude = False
                for exclude_pattern in exclude_patterns:
                    if fnmatch.fnmatch(relative_member_path, exclude_pattern) or fnmatch.fnmatch(
                        member_path, exclude_pattern
                    ):
                        should_exclude = True
                        break

                if should_exclude:
                    continue

                project_file = os.path.join(member_path, "pyproject.toml")
                if not os.path.isfile(project_file):
                    message = (
                        f"Member derived from `{path_spec}` of field "
                        f"`tool.hatch.envs.{self.env.name}.workspace.members` is not a project (no `pyproject.toml` "
                        f"file): {member_path}"
                    )
                    raise OSError(message)

                members_found = True
                if member_path in member_paths:
                    message = (
                        f"Member derived from `{path_spec}` of field "
                        f"`tool.hatch.envs.{self.env.name}.workspace.members` is a duplicate: {member_path}"
                    )
                    raise ValueError(message)

                project = Project(Path(member_path), locate=False)
                project.set_app(self.env.app)
                member_paths[member_path] = WorkspaceMember(project, features=data["features"])

            if not members_found:
                message = (
                    f"No members could be derived from `{path_spec}` of field "
                    f"`tool.hatch.envs.{self.env.name}.workspace.members`: {absolute_path}"
                )
                raise OSError(message)

        return list(member_paths.values())


class WorkspaceMember:
    def __init__(self, project: Project, *, features: tuple[str]):
        self.project = project
        self.features = features
        self._last_modified: float

    @cached_property
    def name(self) -> str:
        return self.project.metadata.name

    @cached_property
    def has_static_dependencies(self) -> bool:
        return self.project.has_static_dependencies

    def get_dependencies(self) -> tuple[list[str], dict[str, list[str]]]:
        return self.project.get_dependencies()

    @property
    def last_modified(self) -> float:
        """Get the last modification time of the member's pyproject.toml."""
        import os

        pyproject_path = self.project.location / "pyproject.toml"
        if pyproject_path.exists():
            return os.path.getmtime(pyproject_path)
        return 0.0

    def get_editable_requirement(self, *, editable: bool = True) -> str:
        """Get the requirement string for this workspace member."""
        uri = self.project.location.as_uri()
        if editable:
            return f"-e {self.name} @ {uri}"
        return f"{self.name} @ {uri}"


def expand_script_commands(env_name, script_name, commands, config, seen, active):
    if script_name in seen:
        return seen[script_name]

    if script_name in active:
        active.append(script_name)

        message = f"Circular expansion detected for field `tool.hatch.envs.{env_name}.scripts`: {' -> '.join(active)}"
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


def find_members(root, relative_components):
    import fnmatch
    import re

    component_matchers = []
    for component in relative_components:
        if any(special in component for special in "*?["):
            pattern = re.compile(fnmatch.translate(component))
            component_matchers.append(lambda entry, pattern=pattern: pattern.search(entry.name))
        else:
            component_matchers.append(lambda entry, component=component: component == entry.name)

    results = list(_recurse_members(root, 0, component_matchers))
    yield from sorted(results, key=os.path.basename)


def _recurse_members(root, matcher_index, matchers):
    if matcher_index == len(matchers):
        yield root
        return

    matcher = matchers[matcher_index]
    with os.scandir(root) as it:
        for entry in it:
            if entry.is_dir() and matcher(entry):
                yield from _recurse_members(entry.path, matcher_index + 1, matchers)
