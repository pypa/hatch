import os
from tempfile import TemporaryDirectory

from hatch.env.utils import add_verbosity_flag
from hatch.utils.env import PythonInfo
from hatch.utils.fs import Path
from hatch.venv.utils import get_random_venv_name


class VirtualEnv:
    IGNORED_ENV_VARS = ('__PYVENV_LAUNCHER__', 'PYTHONHOME')

    def __init__(self, directory, platform, verbosity=0):
        self.directory = directory
        self.platform = platform
        self.verbosity = verbosity
        self.python_info = PythonInfo(platform)

        self._env_vars_to_restore = {}
        self._executables_directory = None

    def activate(self):
        self._env_vars_to_restore['VIRTUAL_ENV'] = os.environ.pop('VIRTUAL_ENV', None)
        os.environ['VIRTUAL_ENV'] = str(self.directory)

        old_path = os.environ.pop('PATH', None)
        self._env_vars_to_restore['PATH'] = old_path
        if old_path is None:
            os.environ['PATH'] = str(self.executables_directory)
        else:
            os.environ['PATH'] = f'{self.executables_directory}{os.pathsep}{old_path}'

        for env_var in self.IGNORED_ENV_VARS:
            self._env_vars_to_restore[env_var] = os.environ.pop(env_var, None)

    def deactivate(self):
        for env_var, value in self._env_vars_to_restore.items():
            if value is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = value

        self._env_vars_to_restore.clear()

    def create(self, python, allow_system_packages=False):
        # WARNING: extremely slow import
        from virtualenv import cli_run

        self.directory.ensure_parent_dir_exists()

        command = [str(self.directory), '--no-download', '--no-periodic-update', '--python', python]

        if allow_system_packages:
            command.append('--system-site-packages')

        # Decrease verbosity since the virtualenv CLI defaults to something like +2 verbosity
        add_verbosity_flag(command, self.verbosity, adjustment=-1)

        cli_run(command)

    def remove(self):
        self.directory.remove()

    def exists(self):
        return self.directory.is_dir()

    @property
    def executables_directory(self):
        if self._executables_directory is None:
            exe_dir = self.directory / ('Scripts' if self.platform.windows else 'bin')
            if exe_dir.is_dir():
                self._executables_directory = exe_dir
            # PyPy
            elif self.platform.windows:
                exe_dir = self.directory / 'bin'
                if exe_dir.is_dir():
                    self._executables_directory = exe_dir
                else:
                    raise OSError(f'Unable to locate executables directory within: {self.directory}')
            # Debian
            elif (self.directory / 'local').is_dir():  # no cov
                exe_dir = self.directory / 'local' / 'bin'
                if exe_dir.is_dir():
                    self._executables_directory = exe_dir
                else:
                    raise OSError(f'Unable to locate executables directory within: {self.directory}')
            else:
                raise OSError(f'Unable to locate executables directory within: {self.directory}')

        return self._executables_directory

    @property
    def environment(self):
        return self.python_info.environment

    @property
    def sys_path(self):
        return self.python_info.sys_path

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.deactivate()


class TempVirtualEnv(VirtualEnv):
    def __init__(self, parent_python, platform, verbosity=0):
        self.parent_python = parent_python
        self.parent_dir = TemporaryDirectory()
        directory = Path(self.parent_dir.name).resolve() / get_random_venv_name()

        super().__init__(directory, platform, verbosity)

    def remove(self):
        super().remove()
        self.parent_dir.cleanup()

    def __enter__(self):
        self.create(self.parent_python)
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        self.remove()
