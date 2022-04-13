from ...env.utils import ensure_valid_environment
from .plugin.interface import EnvironmentCollectorInterface


class DefaultEnvironmentCollector(EnvironmentCollectorInterface):
    PLUGIN_NAME = 'default'

    def get_initial_config(self):
        config = {}
        ensure_valid_environment(config)

        return {'default': config}
