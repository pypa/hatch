import os

from hatch.env.plugin.interface import EnvironmentInterface
from hatch.utils.env import PythonInfo


class SystemEnvironment(EnvironmentInterface):
    PLUGIN_NAME = 'system'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.python_info = PythonInfo(self.platform)
        self.install_indicator = self.data_directory / str(self.root).encode('utf-8').hex()

    def find(self):
        return os.path.dirname(os.path.dirname(self.system_python))

    def create(self) -> None:
        self.install_indicator.touch()

    def remove(self) -> None:
        self.install_indicator.remove()

    def exists(self):
        return self.install_indicator.is_file()

    def install_project(self) -> None:
        self.platform.check_command(self.construct_pip_install_command([self.apply_features(str(self.root))]))

    def install_project_dev_mode(self) -> None:
        self.platform.check_command(
            self.construct_pip_install_command(['--editable', self.apply_features(str(self.root))])
        )

    def dependencies_in_sync(self) -> bool:
        if not self.dependencies:
            return True

        from hatchling.dep.core import dependencies_in_sync

        return dependencies_in_sync(
            self.dependencies_complex, sys_path=self.python_info.sys_path, environment=self.python_info.environment
        )

    def sync_dependencies(self) -> None:
        self.platform.check_command(self.construct_pip_install_command(self.dependencies))
