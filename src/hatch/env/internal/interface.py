from __future__ import annotations

from functools import cached_property

from hatch.env.virtual import VirtualEnvironment


class InternalEnvironment(VirtualEnvironment):
    @cached_property
    def config(self) -> dict:
        config = {'type': 'virtual', 'template': self.name}
        config.update(self.get_base_config())
        config.update(super().config)
        return config

    def get_base_config(self) -> dict:
        return {}
