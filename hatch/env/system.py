from .plugin.interface import EnvironmentInterface


class SystemEnvironment(EnvironmentInterface):
    PLUGIN_NAME = 'system'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.install_indicator = self.data_directory / str(self.root).encode('utf-8').hex()

    def create(self):
        self.install_indicator.touch()

    def remove(self):
        self.install_indicator.remove()

    def exists(self):
        return self.install_indicator.is_file()

    def install_project(self):
        self.platform.check_command(self.construct_pip_install_command([self.apply_features(str(self.root))]))

    def install_project_dev_mode(self):
        self.platform.check_command(
            self.construct_pip_install_command(['--editable', self.apply_features(str(self.root))])
        )

    def dependencies_in_sync(self):
        if not self.dependencies:
            return True

        from hatchling.dep.core import dependencies_in_sync

        return dependencies_in_sync(self.dependencies_complex)

    def sync_dependencies(self):
        self.platform.check_command(self.construct_pip_install_command(self.dependencies))
