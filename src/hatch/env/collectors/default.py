from __future__ import annotations

from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface
from hatch.env.utils import ensure_valid_environment


class DefaultEnvironmentCollector(EnvironmentCollectorInterface):
    PLUGIN_NAME = 'default'

    def get_initial_config(self) -> dict[str, dict[str, str]]:
        config = {}
        ensure_valid_environment(config)

        return {'default': config}
