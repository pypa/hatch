from .plugin.interface import EnvironmentCollectorInterface


class DefaultEnvironmentCollector(EnvironmentCollectorInterface):
    PLUGIN_NAME = 'default'

    def get_initial_config(self):
        return {'default': {'type': 'virtual'}}
