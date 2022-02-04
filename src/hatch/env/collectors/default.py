from .plugin.interface import EnvironmentCollectorInterface


class DefaultEnvironmentCollector(EnvironmentCollectorInterface):
    PLUGIN_NAME = 'default'

    def get_environment_config(self):
        return {'default': {'type': 'virtual'}}
