from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property

from hatch.env.virtual import VirtualEnvironment


class InternalEnvironment(VirtualEnvironment, ABC):
    @cached_property
    def config(self) -> dict:
        config = {'type': 'virtual', 'template': self.name}
        config.update(self.get_base_config())
        config.update(super().config)
        return config

    @abstractmethod
    def get_base_config(self) -> dict: ...
