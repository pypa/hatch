from __future__ import annotations

from typing import Any


def get_default_config() -> dict[str, Any]:
    return {
        'skip-install': True,
        'installer': 'uv',
        'dependencies': [f'ruff=={RUFF_DEFAULT_VERSION}'],
        'scripts': {
            'format-check': 'ruff format{env:HATCH_FMT_ARGS:} --check --diff {args:.}',
            'format-fix': 'ruff format{env:HATCH_FMT_ARGS:} {args:.}',
            'lint-check': 'ruff check{env:HATCH_FMT_ARGS:} {args:.}',
            'lint-fix': 'ruff check{env:HATCH_FMT_ARGS:} --fix {args:.}',
        },
    }


RUFF_DEFAULT_VERSION: str = '0.4.5'
