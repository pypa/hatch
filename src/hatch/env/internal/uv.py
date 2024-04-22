from __future__ import annotations

from typing import Any


def get_default_config() -> dict[str, Any]:
    return {
        'skip-install': True,
        'installer': 'uv',
    }
