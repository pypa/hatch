from __future__ import annotations

import os
import sys
from functools import cached_property
from typing import TYPE_CHECKING, cast

from hatch.cli.terminal import Terminal
from hatch.config.user import ConfigFile, RootConfig
from hatch.project.core import Project
from hatch.utils.fs import Path
from hatch.utils.platform import Platform
from hatch.utils.runner import ExecutionContext

if TYPE_CHECKING:
    from collections.abc import Generator

    from hatch.dep.core import Dependency
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
        return self.project.get_environment(env_name)

    def prepare_environment(self, environment: EnvironmentInterface, *, keep_env: bool = False):
        self.project.prepare_environment(environment, keep_env=keep_env)

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
                    self.display_info(f"{context.source} [{i}] | {raw_command}")

                command = raw_command
                continue_on_error = context.force_continue
                if raw_command.startswith("- "):
                    continue_on_error = True
                    command = command[2:]

                process = context.env.run_shell_command(command)
                sys.stdout.flush()
                sys.stderr.flush()
                if process.returncode:
                    first_error_code = first_error_code or process.returncode
                    if continue_on_error:
                        continue

                    if context.show_code_on_error:
                        self.abort(f"Failed with exit code: {process.returncode}", code=process.returncode)
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
        keep_env: bool = False,
    ) -> Generator[ExecutionContext, None, None]:
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

                        self.abort(f"Environment `{env_name}` is incompatible: {e}")

                any_compatible = True
                if display_header:
                    self.display_header(environment.name)

                context = ExecutionContext(environment)
                yield context

                self.prepare_environment(environment, keep_env=keep_env)
                self.execute_context(context)

        if incompatible:
            num_incompatible = len(incompatible)
            padding = "\n" if any_compatible else ""
            self.display_warning(
                f"{padding}Skipped {num_incompatible} incompatible environment{'s' if num_incompatible > 1 else ''}:"
            )
            for env_name, reason in incompatible.items():
                self.display_warning(f"{env_name} -> {reason}")

    def execute_context(self, context: ExecutionContext) -> None:
        from hatch.utils.structures import EnvVars

        with EnvVars(context.env_vars):
            self.run_shell_commands(context)

    def ensure_environment_plugin_dependencies(self) -> None:
        self.ensure_plugin_dependencies(
            self.project.config.env_requires_complex, wait_message="Syncing environment plugin requirements"
        )

    def ensure_plugin_dependencies(self, dependencies: list[Dependency], *, wait_message: str) -> None:
        if not dependencies:
            return

        from hatch.dep.sync import InstalledDistributions
        from hatch.env.utils import add_verbosity_flag

        if app_path := os.environ.get("PYAPP"):
            from hatch.utils.env import PythonInfo

            management_command = os.environ["PYAPP_COMMAND_NAME"]
            executable = self.platform.check_command_output([app_path, management_command, "python-path"]).strip()
            python_info = PythonInfo(self.platform, executable=executable)
            distributions = InstalledDistributions(sys_path=python_info.sys_path)
            if distributions.dependencies_in_sync(dependencies):
                return

            pip_command = [app_path, management_command, "pip"]
        else:
            distributions = InstalledDistributions()
            if distributions.dependencies_in_sync(dependencies):
                return

            pip_command = [sys.executable, "-u", "-m", "pip"]

        pip_command.extend(["install", "--disable-pip-version-check"])

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

        return self.data_dir / "env" / environment_type

    def get_python_manager(self, directory: str | None = None):
        from hatch.python.core import PythonManager

        configured_dir = directory or self.config.dirs.python
        if configured_dir == "isolated":
            return PythonManager(self.data_dir / "pythons")

        return PythonManager(Path(configured_dir).expand())

    @cached_property
    def shell_data(self) -> tuple[str, str]:
        from hatch.utils.shells import detect_shell

        return detect_shell(self.platform)

    def abort(self, text="", code=1, **kwargs):
        if text:
            self.display_error(text, **kwargs)
        self.__exit_func(code)
