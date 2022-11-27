from __future__ import annotations

import sys

if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class PluginInterface(Protocol):
    @property
    def root(self) -> str:
        ...

    @property
    def config(self) -> dict:
        ...
