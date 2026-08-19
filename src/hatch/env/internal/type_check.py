from __future__ import annotations

from typing import Any


def get_default_config() -> dict[str, Any]:
    from hatch.env.internal.test import get_default_config as get_test_config

    test_config = get_test_config()
    test_deps = test_config.get("dependencies", [])

    return {
        "installer": "uv",
        "dependencies": [f"pyrefly=={PYREFLY_DEFAULT_VERSION}", *test_deps],
        "scripts": {
            "check": "pyrefly check{env:HATCH_CHECK_TYPES_ARGS:} {args}",
            "check-summarize": "pyrefly check{env:HATCH_CHECK_TYPES_ARGS:} --summarize-errors {args}",
            "coverage": "pyrefly report{env:HATCH_CHECK_TYPES_ARGS:} {args}",
            "config": "pyrefly dump-config {args}",
        },
    }


PYREFLY_DEFAULT_VERSION: str = "1.0.0"
