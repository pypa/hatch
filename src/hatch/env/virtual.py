from base64 import urlsafe_b64encode
from contextlib import contextmanager
from hashlib import sha256
from os.path import isabs

from hatch.env.plugin.interface import EnvironmentInterface
from hatch.utils.fs import Path
from hatch.utils.shells import ShellManager
from hatch.venv.core import TempVirtualEnv, VirtualEnv


class VirtualEnvironment(EnvironmentInterface):
    PLUGIN_NAME = 'virtual'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        project_name = self.metadata.core.name

        hashed_root = sha256(str(self.root).encode('utf-8')).digest()
        checksum = urlsafe_b64encode(hashed_root).decode('utf-8')[:8]
        self.storage_path = self.data_directory / f'{project_name}-{checksum}'

        chosen_directory = self.get_env_var_option('path')
        if chosen_directory:
            self.virtual_env_path = Path(chosen_directory) if isabs(chosen_directory) else self.root / chosen_directory
        else:
            directory = project_name if self.name == 'default' else self.name
            self.virtual_env_path = self.storage_path / directory

        self.virtual_env = VirtualEnv(self.virtual_env_path, self.platform, self.verbosity)
        self.shells = ShellManager(self)

        self._parent_python = None

    @staticmethod
    def get_option_types() -> dict:
        return {'system-packages': bool}

    def activate(self):
        self.virtual_env.activate()

    def deactivate(self):
        self.virtual_env.deactivate()

    def find(self):
        return self.virtual_env_path

    def create(self):
        self.virtual_env.create(self.parent_python, allow_system_packages=self.config.get('system-packages', False))

    def remove(self):
        self.virtual_env.remove()

        # Clean up root directory of all virtual environments belonging to the project
        if self.storage_path.is_dir() and not any(self.storage_path.iterdir()):
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
        with self.get_env_vars(), TempVirtualEnv(self.parent_python, self.platform, self.verbosity):
            self.platform.check_command(self.construct_pip_install_command(dependencies))

            yield

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
