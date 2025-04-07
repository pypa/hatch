from __future__ import annotations

import os
import sys
from functools import cached_property
from typing import TYPE_CHECKING, Any, cast

from hatch.cli.terminal import Terminal
from hatch.config.user import ConfigFile, RootConfig
from hatch.project.core import Project
from hatch.utils.fs import Path
from hatch.utils.platform import Platform
from hatch.utils.runner import ExecutionContext

if TYPE_CHECKING:
    from collections.abc import Generator

    from packaging.requirements import Requirement

    from hatch.env.plugin.interface import EnvironmentInterface


class Application(Terminal):
    def __init__(self, exit_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform = Platform(self.output)
        self.__exit_func = exit_func

        self.config_file = ConfigFile()
        self.quiet = self.verbosity < 0
        self.verbose = self.verbosity > 0

        # Lazily set these as we acquire more knowledge about the environment
        self.data_dir = cast(Path, None)
        self.cache_dir = cast(Path, None)
        self.project = cast(Project, None)
        self.env = cast(str, None)
        self.env_active = cast(str, None)

    @property
    def plugins(self):
        return self.project.plugin_manager

    @property
    def config(self) -> RootConfig:
        return self.config_file.model

    def expand_environments(self, env_name: str) -> list[str]:
        if env_name in self.project.config.internal_matrices:
            return list(self.project.config.internal_matrices[env_name]['envs'])

        if env_name in self.project.config.matrices:
            return list(self.project.config.matrices[env_name]['envs'])

        if env_name in self.project.config.internal_envs:
            return [env_name]

        if env_name in self.project.config.envs:
            return [env_name]

        return []

    def get_environment(self, env_name: str | None = None) -> EnvironmentInterface:
        if env_name is None:
            env_name = self.env

        if env_name in self.project.config.internal_envs:
            config = self.project.config.internal_envs[env_name]
        elif env_name in self.project.config.envs:
            config = self.project.config.envs[env_name]
        else:
            self.abort(f'Unknown environment: {env_name}')

        environment_type = config['type']
        environment_class = self.plugins.environment.get(environment_type)
        if environment_class is None:
            self.abort(f'Environment `{env_name}` has unknown type: {environment_type}')

        from hatch.env.internal import is_isolated_environment

        if self.project.location.is_file():
            data_directory = isolated_data_directory = self.data_dir / 'env' / environment_type / '.scripts'
        elif is_isolated_environment(env_name, config):
            data_directory = isolated_data_directory = self.data_dir / 'env' / '.internal' / env_name
        else:
            data_directory = self.get_env_directory(environment_type)
            isolated_data_directory = self.data_dir / 'env' / environment_type

        self.project.config.finalize_env_overrides(environment_class.get_option_types())

        return environment_class(
            self.project.location,
            self.project.metadata,
            env_name,
            config,
            self.project.config.matrix_variables.get(env_name, {}),
            data_directory,
            isolated_data_directory,
            self.platform,
            self.verbosity,
            self,
        )

    # Ensure that this method is clearly written since it is
    # used for documenting the life cycle of environments.
    def prepare_environment(self, environment: EnvironmentInterface):
        if not environment.exists():
            self.env_metadata.reset(environment)

            with environment.app_status_creation():
                environment.create()

            if not environment.skip_install:
                if environment.pre_install_commands:
                    with environment.app_status_pre_installation():
                        self.run_shell_commands(
                            ExecutionContext(
                                environment,
                                shell_commands=environment.pre_install_commands,
                                source='pre-install',
                                show_code_on_error=True,
                            )
                        )

                with environment.app_status_project_installation():
                    if environment.dev_mode:
                        environment.install_project_dev_mode()
                    else:
                        environment.install_project()

                if environment.post_install_commands:
                    with environment.app_status_post_installation():
                        self.run_shell_commands(
                            ExecutionContext(
                                environment,
                                shell_commands=environment.post_install_commands,
                                source='post-install',
                                show_code_on_error=True,
                            )
                        )

        with environment.app_status_dependency_state_check():
            new_dep_hash = environment.dependency_hash()

        current_dep_hash = self.env_metadata.dependency_hash(environment)
        if new_dep_hash != current_dep_hash:
            with environment.app_status_dependency_installation_check():
                dependencies_in_sync = environment.dependencies_in_sync()

            if not dependencies_in_sync:
                with environment.app_status_dependency_synchronization():
                    environment.sync_dependencies()
                    new_dep_hash = environment.dependency_hash()

            self.env_metadata.update_dependency_hash(environment, new_dep_hash)

    def run_shell_commands(self, context: ExecutionContext) -> None:
        with context.env.command_context():
            try:
                resolved_commands = list(context.env.resolve_commands(context.shell_commands))
            except Exception as e:  # noqa: BLE001
                self.abort(str(e))

            first_error_code = None
            should_display_command = not context.hide_commands and (self.verbose or len(resolved_commands) > 1)
            for i, raw_command in enumerate(resolved_commands, 1):
                if should_display_command:
                    self.display(f'{context.source} [{i}] | {raw_command}')

                command = raw_command
                continue_on_error = context.force_continue
                if raw_command.startswith('- '):
                    continue_on_error = True
                    command = command[2:]

                process = context.env.run_shell_command(command)
                if process.returncode:
                    first_error_code = first_error_code or process.returncode
                    if continue_on_error:
                        continue

                    if context.show_code_on_error:
                        self.abort(f'Failed with exit code: {process.returncode}', code=process.returncode)
                    else:
                        self.abort(code=process.returncode)

            if first_error_code and context.force_continue:
                self.abort(code=first_error_code)

    def runner_context(
        self,
        environments: list[str],
        *,
        ignore_compat: bool = False,
        display_header: bool = False,
    ) -> Generator[ExecutionContext, None, None]:
        from hatch.utils.structures import EnvVars

        if self.verbose or len(environments) > 1:
            display_header = True

        any_compatible = False
        incompatible = {}
        with self.project.ensure_cwd():
            for env_name in environments:
                environment = self.get_environment(env_name)
                if not environment.exists():
                    try:
                        environment.check_compatibility()
                    except Exception as e:  # noqa: BLE001
                        if ignore_compat:
                            incompatible[environment.name] = str(e)
                            continue

                        self.abort(f'Environment `{env_name}` is incompatible: {e}')

                any_compatible = True
                if display_header:
                    self.display_header(environment.name)

                context = ExecutionContext(environment)
                yield context

                self.prepare_environment(environment)
                with EnvVars(context.env_vars):
                    self.run_shell_commands(context)

        if incompatible:
            num_incompatible = len(incompatible)
            padding = '\n' if any_compatible else ''
            self.display_warning(
                f'{padding}Skipped {num_incompatible} incompatible environment{"s" if num_incompatible > 1 else ""}:'
            )
            for env_name, reason in incompatible.items():
                self.display_warning(f'{env_name} -> {reason}')

    def ensure_environment_plugin_dependencies(self) -> None:
        self.ensure_plugin_dependencies(
            self.project.config.env_requires_complex, wait_message='Syncing environment plugin requirements'
        )

    def ensure_plugin_dependencies(self, dependencies: list[Requirement], *, wait_message: str) -> None:
        if not dependencies:
            return

        from hatch.env.utils import add_verbosity_flag
        from hatchling.dep.core import dependencies_in_sync

        if app_path := os.environ.get('PYAPP'):
            from hatch.utils.env import PythonInfo

            management_command = os.environ['PYAPP_COMMAND_NAME']
            executable = self.platform.check_command_output([app_path, management_command, 'python-path']).strip()
            python_info = PythonInfo(self.platform, executable=executable)
            if dependencies_in_sync(dependencies, sys_path=python_info.sys_path):
                return

            pip_command = [app_path, management_command, 'pip']
        else:
            if dependencies_in_sync(dependencies):
                return

            pip_command = [sys.executable, '-u', '-m', 'pip']

        pip_command.extend(['install', '--disable-pip-version-check'])

        # Default to -1 verbosity
        add_verbosity_flag(pip_command, self.verbosity, adjustment=-1)

        pip_command.extend(str(dependency) for dependency in dependencies)

        with self.status(wait_message):
            self.platform.check_command(pip_command)

    def get_env_directory(self, environment_type):
        directories = self.config.dirs.env

        if environment_type in directories:
            path = Path(directories[environment_type]).expand()
            if os.path.isabs(path):
                return path

            return self.project.location / path

        return self.data_dir / 'env' / environment_type

    def get_python_manager(self, directory: str | None = None):
        from hatch.python.core import PythonManager

        configured_dir = directory or self.config.dirs.python
        if configured_dir == 'isolated':
            return PythonManager(self.data_dir / 'pythons')

        return PythonManager(Path(configured_dir).expand())

    @cached_property
    def shell_data(self) -> tuple[str, str]:
        from hatch.utils.shells import detect_shell

        return detect_shell(self.platform)

    @cached_property
    def env_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(self.data_dir / 'env' / '.metadata', self.project.location)

    def abort(self, text='', code=1, **kwargs):
        if text:
            self.display_error(text, **kwargs)
        self.__exit_func(code)


class EnvironmentMetadata:
    def __init__(self, data_dir: Path, project_path: Path):
        self.__data_dir = data_dir
        self.__project_path = project_path

    def dependency_hash(self, environment: EnvironmentInterface) -> str:
        return self._read(environment).get('dependency_hash', '')

    def update_dependency_hash(self, environment: EnvironmentInterface, dependency_hash: str) -> None:
        metadata = self._read(environment)
        metadata['dependency_hash'] = dependency_hash
        self._write(environment, metadata)

    def reset(self, environment: EnvironmentInterface) -> None:
        self._metadata_file(environment).unlink(missing_ok=True)

    def _read(self, environment: EnvironmentInterface) -> dict[str, Any]:
        import json

        metadata_file = self._metadata_file(environment)
        if not metadata_file.is_file():
            return {}

        return json.loads(metadata_file.read_text())

    def _write(self, environment: EnvironmentInterface, metadata: dict[str, Any]) -> None:
        import json

        metadata_file = self._metadata_file(environment)
        metadata_file.parent.ensure_dir_exists()
        metadata_file.write_text(json.dumps(metadata))

    def _metadata_file(self, environment: EnvironmentInterface) -> Path:
        from hatch.env.internal import is_isolated_environment

        if is_isolated_environment(environment.name, environment.config):
            return self.__data_dir / '.internal' / f'{environment.name}.json'

        return self._storage_dir / environment.config['type'] / f'{environment.name}.json'

    @cached_property
    def _storage_dir(self) -> Path:
        return self.__data_dir / self.__project_path.id
