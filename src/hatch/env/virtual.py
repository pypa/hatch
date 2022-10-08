from base64 import urlsafe_b64encode
from contextlib import contextmanager
from hashlib import sha256
from os.path import isabs

from hatch.env.plugin.interface import EnvironmentInterface
from hatch.utils.fs import Path
from hatch.utils.shells import ShellManager
from hatch.venv.core import VirtualEnv


class VirtualEnvironment(EnvironmentInterface):
    PLUGIN_NAME = 'virtual'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        project_name = self.metadata.name
        venv_name = project_name if self.name == 'default' else self.name

        # Always compute the app path for build environments
        hashed_root = sha256(str(self.root).encode('utf-8')).digest()
        checksum = urlsafe_b64encode(hashed_root).decode('utf-8')[:8]
        app_storage_path = self.data_directory / project_name / checksum
        app_virtual_env_path = app_storage_path / venv_name

        # Explicit path
        chosen_directory = self.get_env_var_option('path') or self.config.get('path', '')
        if chosen_directory:
            self.storage_path = app_storage_path
            self.virtual_env_path = (
                Path(chosen_directory) if isabs(chosen_directory) else (self.root / chosen_directory).resolve()
            )
        # Conditions requiring a flat structure
        elif self.root in self.data_directory.parents or self.data_directory == Path.home() / '.virtualenvs':
            self.storage_path = self.data_directory
            self.virtual_env_path = self.storage_path / venv_name
        # Otherwise the standard app path
        else:
            self.storage_path = app_storage_path
            self.virtual_env_path = app_virtual_env_path

        self.virtual_env = VirtualEnv(self.virtual_env_path, self.platform, self.verbosity)
        self.build_virtual_env = VirtualEnv(
            app_virtual_env_path.parent / f'{app_virtual_env_path.name}-build', self.platform, self.verbosity
        )
        self.shells = ShellManager(self)

        self._parent_python = None

    @staticmethod
    def get_option_types() -> dict:
        return {'system-packages': bool, 'path': bool}

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

        self.virtual_env.create(self.parent_python, allow_system_packages=self.config.get('system-packages', False))

    def remove(self):
        self.virtual_env.remove()
        self.build_virtual_env.remove()

        # Clean up root directory of all virtual environments belonging to the project
        if self.storage_path != Path.home() / '.virtualenvs' and self.storage_path.is_dir():
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

    def enter_shell(self, name, path, args):
        shell_executor = getattr(self.shells, f'enter_{name}', None)
        if shell_executor is None:
            # Manually activate in lieu of an activation script
            with self.safe_activation():
                self.platform.exit_with_command([path, *args])
        else:
            with self.get_env_vars():
                shell_executor(path, args, self.virtual_env.executables_directory)

    def check_compatibility(self):
        super().check_compatibility()

        python_choice = self.config.get('python')
        if not python_choice:
            return

        try:
            if self.parent_python:
                return
        except Exception:
            pass

        raise OSError(f'cannot locate Python: {python_choice}')

    @property
    def parent_python(self):
        if self._parent_python is None:
            python_choice = self.config.get('python')
            if not python_choice:
                python_executable = self.system_python
            else:
                from virtualenv.discovery.builtin import get_interpreter

                python_executable = get_interpreter(python_choice, ()).executable

            self._parent_python = python_executable

        return self._parent_python

    @contextmanager
    def safe_activation(self):
        # Set user-defined environment variables first so ours take precedence
        with self.get_env_vars(), self:
            yield
