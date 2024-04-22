from __future__ import annotations

from typing import Any


def get_default_config() -> dict[str, Any]:
    return {
        'skip-install': True,
        'installer': 'uv',
        'dependencies': ['build[virtualenv]>=1.0.3'],
        'scripts': {
            'build-all': 'python -m build',
            'build-sdist': 'python -m build --sdist',
            'build-wheel': 'python -m build --wheel',
        },
    }
