from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface
from hatch.env.internal import get_internal_env_config
from hatch.env.utils import ensure_valid_environment


class DefaultEnvironmentCollector(EnvironmentCollectorInterface):
    PLUGIN_NAME = 'default'

    def get_initial_config(self):  # noqa: PLR6301
        default_config = {}
        ensure_valid_environment(default_config)

        return {'default': default_config, **get_internal_env_config()}
