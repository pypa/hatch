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

if TYPE_CHECKING:
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

    def get_environment(self, env_name: str | None = None) -> EnvironmentInterface:
        if env_name is None:
            env_name = self.env

        if env_name in self.project.config.internal_envs:
            config = self.project.config.internal_envs[env_name]
        elif env_name not in self.project.config.envs:
            self.abort(f'Unknown environment: {env_name}')
        else:
            config = self.project.config.envs[env_name]

        environment_type = config['type']
        environment_class = self.plugins.environment.get(environment_type)
        if environment_class is None:
            self.abort(f'Environment `{env_name}` has unknown type: {environment_type}')

        if is_isolated_environment(env_name, config):
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
            self.get_safe_application(),
        )

    # Ensure that this method is clearly written since it is
    # used for documenting the life cycle of environments.
    def prepare_environment(self, environment: EnvironmentInterface):
        if not environment.exists():
            self.env_metadata.reset(environment)

            with self.status(f'Creating environment: {environment.name}'):
                environment.create()

            if not environment.skip_install:
                if environment.pre_install_commands:
                    with self.status('Running pre-installation commands'):
                        self.run_shell_commands(environment, environment.pre_install_commands, source='pre-install')

                if environment.dev_mode:
                    with self.status('Installing project in development mode'):
                        environment.install_project_dev_mode()
                else:
                    with self.status('Installing project'):
                        environment.install_project()

                if environment.post_install_commands:
                    with self.status('Running post-installation commands'):
                        self.run_shell_commands(environment, environment.post_install_commands, source='post-install')

        new_dep_hash = environment.dependency_hash()
        current_dep_hash = self.env_metadata.dependency_hash(environment)
        if new_dep_hash != current_dep_hash:
            with self.status('Checking dependencies'):
                dependencies_in_sync = environment.dependencies_in_sync()

            if not dependencies_in_sync:
                with self.status('Syncing dependencies'):
                    environment.sync_dependencies()
                    new_dep_hash = environment.dependency_hash()

            self.env_metadata.update_dependency_hash(environment, new_dep_hash)

    def run_shell_commands(
        self,
        environment: EnvironmentInterface,
        commands: list[str],
        source='cmd',
        *,
        force_continue=False,
        show_code_on_error=True,
    ):
        with environment.command_context():
            try:
                resolved_commands = list(environment.resolve_commands(commands))
            except Exception as e:  # noqa: BLE001
                self.abort(str(e))

            first_error_code = None
            should_display_command = self.verbose or len(resolved_commands) > 1
            for i, raw_command in enumerate(resolved_commands, 1):
                if should_display_command:
                    self.display(f'{source} [{i}] | {raw_command}')

                command = raw_command
                continue_on_error = force_continue
                if raw_command.startswith('- '):
                    continue_on_error = True
                    command = command[2:]

                process = environment.run_shell_command(command)
                if process.returncode:
                    first_error_code = first_error_code or process.returncode
                    if continue_on_error:
                        continue

                    if show_code_on_error:
                        self.abort(f'Failed with exit code: {process.returncode}', code=process.returncode)
                    else:
                        self.abort(code=process.returncode)

            if first_error_code and force_continue:
                self.abort(code=first_error_code)

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

        pip_command.extend(['install', '--disable-pip-version-check', '--no-python-version-warning'])

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
        import shellingham

        try:
            return shellingham.detect_shell()
        except shellingham.ShellDetectionFailure:
            path = self.platform.default_shell
            return Path(path).stem, path

    @cached_property
    def env_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(self.data_dir / 'env' / '.metadata', self.project.location)

    @staticmethod
    def is_internal_default_environment(env_name: str, config: dict[str, Any]) -> bool:
        from hatch.env.internal import get_internal_env_config

        internal_config = get_internal_env_config().get(env_name)
        if not internal_config:
            return False

        # Only consider things that would modify the actual installation, other options like extra scripts don't matter
        for key in ('dependencies', 'extra-dependencies', 'features'):
            if config.get(key) != internal_config.get(key):
                return False

        return True

    def abort(self, text='', code=1, **kwargs):
        if text:
            self.display_error(text, **kwargs)
        self.__exit_func(code)

    def get_safe_application(self) -> SafeApplication:
        return SafeApplication(self)


class SafeApplication:
    def __init__(self, app: Application):
        self.abort = app.abort
        self.display = app.display
        self.display_critical = app.display_critical
        self.display_info = app.display_info
        self.display_error = app.display_error
        self.display_success = app.display_success
        self.display_waiting = app.display_waiting
        self.display_warning = app.display_warning
        self.display_debug = app.display_debug
        self.display_mini_header = app.display_mini_header
        # Divergence from what the backend provides
        self.prompt = app.prompt
        self.confirm = app.confirm
        self.status = app.status
        self.status_if = app.status_if


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
        if is_isolated_environment(environment.name, environment.config):
            return self.__data_dir / '.internal' / f'{environment.name}.json'

        return self._storage_dir / environment.config['type'] / f'{environment.name}.json'

    @cached_property
    def _storage_dir(self) -> Path:
        from base64 import urlsafe_b64encode
        from hashlib import sha256

        return self.__data_dir / urlsafe_b64encode(sha256(str(self.__project_path).encode()).digest())[:8].decode()


def is_isolated_environment(env_name: str, config: dict[str, Any]) -> bool:
    # Provide super isolation and immunity to project-level environment removal only when the environment:
    #
    # 1. Does not require the project being installed
    # 2. The default configuration is used
    #
    # For example, the environment for static analysis depends only on Ruff at a specific default
    # version. This environment does not require the project and can be reused by every project to
    # improve responsiveness. However, if the user for some reason chooses to override the dependencies
    # to use a different version of Ruff, then the project would get its own environment.
    if not config.get('skip-install', False):
        return False

    from hatch.env.internal import get_internal_env_config

    internal_config = get_internal_env_config().get(env_name)
    if not internal_config:
        return False

    # Only consider things that would modify the actual installation, other options like extra scripts don't matter
    for key in ('dependencies', 'extra-dependencies', 'features'):
        if config.get(key) != internal_config.get(key):
            return False

    return True
