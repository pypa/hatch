from __future__ import annotations

import os
import sys
from contextlib import contextmanager, nullcontext, suppress
from functools import cached_property
from os.path import isabs
from typing import TYPE_CHECKING, Callable

from hatch.config.constants import AppEnvVars
from hatch.env.plugin.interface import EnvironmentInterface
from hatch.env.utils import add_verbosity_flag
from hatch.utils.fs import Path
from hatch.utils.shells import ShellManager
from hatch.utils.structures import EnvVars
from hatch.venv.core import UVVirtualEnv, VirtualEnv

if TYPE_CHECKING:
    from collections.abc import Iterable

    from packaging.specifiers import SpecifierSet
    from virtualenv.discovery.py_info import PythonInfo

    from hatch.python.core import PythonManager


class VirtualEnvironment(EnvironmentInterface):
    PLUGIN_NAME = 'virtual'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        project_id = self.root.id
        project_is_script = self.root.is_file()
        project_name = (
            project_id
            if project_is_script
            else self.metadata.name
            if 'project' in self.metadata.config
            else f'{project_id}-unmanaged'
        )
        venv_name = project_name if self.name == 'default' else self.name

        # Conditions requiring a flat structure for build env
        if (
            self.isolated_data_directory == self.platform.home / '.virtualenvs'
            or self.root in self.isolated_data_directory.resolve().parents
        ):
            app_virtual_env_path = self.isolated_data_directory / venv_name
        else:
            app_virtual_env_path = self.isolated_data_directory / project_name / project_id / venv_name

        # Explicit path
        chosen_directory = self.get_env_var_option('path') or self.config.get('path', '')
        if chosen_directory:
            self.storage_path = self.data_directory / project_name / project_id
            self.virtual_env_path = (
                Path(chosen_directory) if isabs(chosen_directory) else (self.root / chosen_directory).resolve()
            )
        elif project_is_script:
            self.storage_path = self.virtual_env_path = self.isolated_data_directory / venv_name
        # Conditions requiring a flat structure
        elif (
            self.data_directory == self.platform.home / '.virtualenvs'
            or self.root in self.data_directory.resolve().parents
        ):
            self.storage_path = self.data_directory
            self.virtual_env_path = self.storage_path / venv_name
        # Otherwise the defined app path
        else:
            self.storage_path = self.data_directory / project_name / project_id
            self.virtual_env_path = self.storage_path / venv_name

        self.virtual_env = self.virtual_env_cls(self.virtual_env_path, self.platform, self.verbosity)
        self.build_virtual_env = self.virtual_env_cls(
            app_virtual_env_path.parent / f'{app_virtual_env_path.name}-build', self.platform, self.verbosity
        )
        self.shells = ShellManager(self)

        self._parent_python = None

    @cached_property
    def use_uv(self) -> bool:
        return self.installer == 'uv' or bool(self.explicit_uv_path)

    @cached_property
    def installer(self) -> str:
        return self.config.get('installer', 'pip')

    @cached_property
    def explicit_uv_path(self) -> str:
        return self.get_env_var_option('uv_path') or self.config.get('uv-path', '')

    @cached_property
    def virtual_env_cls(self) -> type[VirtualEnv]:
        return UVVirtualEnv if self.use_uv else VirtualEnv

    def expose_uv(self):
        if not (self.use_uv or self.uv_path):
            return nullcontext()

        return EnvVars({'HATCH_UV': self.uv_path})

    @cached_property
    def uv_path(self) -> str:
        if self.explicit_uv_path:
            return self.explicit_uv_path

        from hatch.env.internal import is_default_environment

        env_name = 'hatch-uv'
        if not (
            # Prevent recursive loop
            self.name == env_name
            # Only if dependencies have been set by the user
            or is_default_environment(env_name, self.app.project.config.internal_envs[env_name])
        ):
            uv_env = self.app.get_environment(env_name)
            self.app.prepare_environment(uv_env)
            with uv_env:
                return self.platform.modules.shutil.which('uv')

        import sysconfig

        scripts_dir = sysconfig.get_path('scripts')
        old_path = os.environ.get('PATH', os.defpath)
        new_path = f'{scripts_dir}{os.pathsep}{old_path}'
        return self.platform.modules.shutil.which('uv', path=new_path)

    @staticmethod
    def get_option_types() -> dict:
        return {'system-packages': bool, 'path': str, 'python-sources': list, 'installer': str, 'uv-path': str}

    def activate(self):
        self.virtual_env.activate()

    def deactivate(self):
        self.virtual_env.deactivate()

    def find(self):
        return self.virtual_env_path

    def create(self):
        if self.root in self.storage_path.parents:
            # Although it would be nice to support Mercurial, only Git supports multiple ignore files. See:
            # https://github.com/pytest-dev/pytest/issues/3286#issuecomment-421439197
            vcs_ignore_file = self.storage_path / '.gitignore'
            if not vcs_ignore_file.is_file():
                vcs_ignore_file.ensure_parent_dir_exists()
                vcs_ignore_file.write_text(
                    """\
# This file was automatically created by Hatch
*
"""
                )

        with self.expose_uv():
            self.virtual_env.create(self.parent_python, allow_system_packages=self.config.get('system-packages', False))

    def remove(self):
        self.virtual_env.remove()
        self.build_virtual_env.remove()

        # Clean up root directory of all virtual environments belonging to the project
        if self.storage_path != self.platform.home / '.virtualenvs' and self.storage_path.is_dir():
            entries = [entry.name for entry in self.storage_path.iterdir()]
            if not entries or (entries == ['.gitignore'] and self.root in self.storage_path.parents):
                self.storage_path.remove()

    def exists(self):
        return self.virtual_env.exists()

    def install_project(self):
        with self.safe_activation():
            self.platform.check_command(self.construct_pip_install_command([self.apply_features(str(self.root))]))

    def install_project_dev_mode(self):
        with self.safe_activation():
            self.platform.check_command(
                self.construct_pip_install_command(['--editable', self.apply_features(str(self.root))])
            )

    def dependencies_in_sync(self):
        if not self.dependencies:
            return True

        from hatchling.dep.core import dependencies_in_sync

        with self.safe_activation():
            return dependencies_in_sync(
                self.dependencies_complex, sys_path=self.virtual_env.sys_path, environment=self.virtual_env.environment
            )

    def sync_dependencies(self):
        with self.safe_activation():
            self.platform.check_command(self.construct_pip_install_command(self.dependencies))

    @contextmanager
    def build_environment(self, dependencies):
        from packaging.requirements import Requirement

        from hatchling.dep.core import dependencies_in_sync

        if not self.build_environment_exists():
            with self.expose_uv():
                self.build_virtual_env.create(self.parent_python)

        with self.get_env_vars(), self.build_virtual_env:
            if not dependencies_in_sync(
                [Requirement(d) for d in dependencies],
                sys_path=self.build_virtual_env.sys_path,
                environment=self.build_virtual_env.environment,
            ):
                self.platform.check_command(self.construct_pip_install_command(dependencies))

            yield

    def build_environment_exists(self):
        return self.build_virtual_env.exists()

    @contextmanager
    def command_context(self):
        with self.safe_activation():
            yield

    def construct_pip_install_command(self, args: list[str]):
        if not self.use_uv:
            return super().construct_pip_install_command(args)

        command = [self.uv_path, 'pip', 'install']

        # Default to -1 verbosity
        add_verbosity_flag(command, self.verbosity, adjustment=-1)

        command.extend(args)
        return command

    def enter_shell(self, name: str, path: str, args: Iterable[str]):
        shell_executor = getattr(self.shells, f'enter_{name}', None)
        if shell_executor is None:
            # Manually activate in lieu of an activation script
            with self.safe_activation():
                self.platform.exit_with_command([path, *args])
        else:
            with self.expose_uv(), self.get_env_vars():
                shell_executor(path, args, self.virtual_env.executables_directory)

    def check_compatibility(self):
        super().check_compatibility()

        python_version = self.config.get('python', '')
        if (
            os.environ.get(AppEnvVars.PYTHON)
            or self._find_existing_interpreter(python_version) is not None
            or self._get_available_distribution(python_version) is not None
        ):
            return

        message = (
            f'cannot locate Python: {python_version}'
            if python_version
            else 'no compatible Python distribution available'
        )
        raise OSError(message)

    @cached_property
    def _preferred_python_version(self):
        return f'{sys.version_info.major}.{sys.version_info.minor}'

    @cached_property
    def parent_python(self):
        if python_choice := self.config.get('python', ''):
            return self._get_concrete_interpreter_path(python_choice)

        if explicit_default := os.environ.get(AppEnvVars.PYTHON):
            return sys.executable if explicit_default == 'self' else explicit_default

        return self._get_concrete_interpreter_path()

    @cached_property
    def python_manager(self) -> PythonManager:
        from hatch.python.core import PythonManager

        return PythonManager(self.isolated_data_directory / '.pythons')

    def get_interpreter_resolver_env(self) -> dict[str, str]:
        env = dict(os.environ)
        python_dirs = [str(dist.python_path.parent) for dist in self.python_manager.get_installed().values()]
        if not python_dirs:
            return env

        internal_path = os.pathsep.join(python_dirs)
        old_path = env.pop('PATH', None)
        env['PATH'] = internal_path if old_path is None else f'{old_path}{os.pathsep}{internal_path}'

        return env

    def upgrade_possible_internal_python(self, python_path: str) -> None:
        if 'internal' not in self._python_sources:
            return

        for dist in self.python_manager.get_installed().values():
            if dist.python_path == Path(python_path):
                if dist.needs_update():
                    with self.app.status(f'Updating Python distribution: {dist.name}'):
                        self.python_manager.install(dist.name)

                break

    def _interpreter_is_compatible(self, interpreter: PythonInfo) -> bool:
        return (
            interpreter.executable
            and self._is_stable_path(interpreter.executable)
            and (self.skip_install or self._python_constraint.contains(interpreter.version_str))
        )

    def _get_concrete_interpreter_path(self, python_version: str = '') -> str | None:
        known_resolvers = self._python_resolvers()
        resolvers = [known_resolvers[source] for source in self._python_sources]
        if python_version:
            for resolver in resolvers:
                if (concrete_path := resolver(python_version)) is not None:
                    return concrete_path
        else:
            # Prefer the Python version Hatch is currently using
            for resolver in resolvers:
                if (concrete_path := resolver(self._preferred_python_version)) is not None:
                    return concrete_path

            # Fallback to whatever is compatible
            for resolver in resolvers:
                if (concrete_path := resolver('')) is not None:
                    return concrete_path

        return None

    def _resolve_external_interpreter_path(self, python_version: str) -> str | None:
        if (existing_path := self._find_existing_interpreter(python_version)) is not None:
            self.upgrade_possible_internal_python(existing_path)
            return existing_path

        return None

    def _resolve_internal_interpreter_path(self, python_version: str) -> str | None:
        if (available_distribution := self._get_available_distribution(python_version)) is not None:
            with self.app.status(f'Installing Python distribution: {available_distribution}'):
                dist = self.python_manager.install(available_distribution)

            return str(dist.python_path)

        return None

    def _find_existing_interpreter(self, python_version: str = '') -> str | None:
        from virtualenv.discovery import builtin as virtualenv_discovery

        propose_interpreters = virtualenv_discovery.propose_interpreters

        def _patched_propose_interpreters(*args, **kwargs):
            for interpreter, impl_must_match in propose_interpreters(*args, **kwargs):
                if not self._interpreter_is_compatible(interpreter):
                    continue

                yield interpreter, impl_must_match

        virtualenv_discovery.propose_interpreters = _patched_propose_interpreters
        try:
            python_info = virtualenv_discovery.get_interpreter(
                python_version, (), env=self.get_interpreter_resolver_env()
            )
            if python_info is not None:
                return python_info.executable
        finally:
            virtualenv_discovery.propose_interpreters = propose_interpreters

    def _get_available_distribution(self, python_version: str = '') -> str | None:
        from hatch.python.resolve import get_compatible_distributions

        compatible_distributions = get_compatible_distributions()
        for installed_distribution in self.python_manager.get_installed():
            compatible_distributions.pop(installed_distribution, None)

        if not python_version:
            # Only try providing CPython distributions
            available_distributions = [d for d in compatible_distributions if not d.startswith('pypy')]

            # Prioritize the version that Hatch is currently using, if available
            with suppress(ValueError):
                available_distributions.remove(self._preferred_python_version)
                available_distributions.append(self._preferred_python_version)

            # Latest first
            available_distributions.reverse()
        elif python_version in compatible_distributions:
            available_distributions = [python_version]
        else:
            return None

        for available_distribution in available_distributions:
            minor_version = (
                available_distribution.replace('pypy', '', 1)
                if available_distribution.startswith('pypy')
                else available_distribution
            )
            if not self._python_constraint.contains(minor_version):
                continue

            return available_distribution

        return None

    def _is_stable_path(self, executable: str) -> bool:
        path = Path(executable).resolve()
        parents = path.parents

        # https://pypa.github.io/pipx/how-pipx-works/
        if (Path.home() / '.local' / 'pipx' / 'venvs') in parents:
            return False

        from platformdirs import user_data_dir

        # https://github.com/ofek/pyapp/blob/v0.13.0/src/app.rs#L27
        if Path(user_data_dir('pyapp', appauthor=False)) in parents:
            return False

        # via Windows store
        if self.platform.windows and str(path).endswith('WindowsApps\\python.exe'):
            return False

        # via Homebrew
        return not (self.platform.macos and Path('/usr/local/Cellar') in parents)

    @cached_property
    def _python_sources(self) -> list[str]:
        return self.config.get('python-sources') or ['external', 'internal']

    def _python_resolvers(self) -> dict[str, Callable[[str], str | None]]:
        return {
            'external': self._resolve_external_interpreter_path,
            'internal': self._resolve_internal_interpreter_path,
        }

    @cached_property
    def _python_constraint(self) -> SpecifierSet:
        from packaging.specifiers import SpecifierSet

        # Note that we do not support this field being dynamic because if we were to set up the
        # build environment to retrieve the field then we would be stuck because we need to use
        # a satisfactory version to set up the environment
        return SpecifierSet(self.metadata.config.get('project', {}).get('requires-python', ''))

    @contextmanager
    def safe_activation(self):
        # In order of precedence:
        # - This environment
        # - UV
        # - User-defined environment variables
        with self.get_env_vars(), self.expose_uv(), self:
            yield
