from __future__ import annotations

from typing import Any


def get_default_config() -> dict[str, Any]:
    return {
        "skip-install": True,
        "installer": "uv",
        "dependencies": [f"ruff=={RUFF_DEFAULT_VERSION}"],
        "scripts": {
            "format-check": "ruff format{env:HATCH_FMT_ARGS:}{env:HATCH_CHECK_FMT_ARGS:} --check --diff {args:.}",
            "format-fix": "ruff format{env:HATCH_FMT_ARGS:}{env:HATCH_CHECK_FMT_ARGS:} {args:.}",
            "lint-check": "ruff check{env:HATCH_FMT_ARGS:}{env:HATCH_CHECK_CODE_ARGS:} {args:.}",
            "lint-fix": "ruff check{env:HATCH_FMT_ARGS:}{env:HATCH_CHECK_CODE_ARGS:} --fix {args:.}",
        },
    }


def get_check_code_config() -> dict[str, Any]:
    return {
        "skip-install": True,
        "installer": "uv",
        "dependencies": [f"ruff=={RUFF_DEFAULT_VERSION}"],
        "scripts": {
            "lint-check": "ruff check{env:HATCH_CHECK_CODE_ARGS:} {args:.}",
            "lint-fix": "ruff check{env:HATCH_CHECK_CODE_ARGS:} --fix {args:.}",
        },
    }


def get_check_fmt_config() -> dict[str, Any]:
    return {
        "skip-install": True,
        "installer": "uv",
        "dependencies": [f"ruff=={RUFF_DEFAULT_VERSION}"],
        "scripts": {
            "format-check": "ruff format{env:HATCH_CHECK_FMT_ARGS:} --check --diff {args:.}",
            "format-fix": "ruff format{env:HATCH_CHECK_FMT_ARGS:} {args:.}",
        },
    }


RUFF_DEFAULT_VERSION: str = "0.13.2"
