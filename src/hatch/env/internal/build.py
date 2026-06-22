from __future__ import annotations

from typing import Any


def get_default_config() -> dict[str, Any]:
    from hatch.env.internal import default_installer

    return {
        "skip-install": True,
        "builder": True,
        "installer": default_installer(),
    }
