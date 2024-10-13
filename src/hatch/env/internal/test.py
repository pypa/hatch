from __future__ import annotations

from typing import Any


def get_default_config() -> dict[str, Any]:
    return {
        'installer': 'uv',
        'dependencies': [
            'coverage-enable-subprocess==1.0',
            'coverage[toml]~=7.4',
            'pytest~=8.1',
            'pytest-mock~=3.12',
            'pytest-randomly~=3.15',
            'pytest-rerunfailures~=14.0',
            'pytest-xdist[psutil]~=3.5',
        ],
        'scripts': {
            'run': 'pytest{env:HATCH_TEST_ARGS:} {args}',
            'run-cov': 'coverage run -m pytest{env:HATCH_TEST_ARGS:} {args}',
            'cov-combine': 'coverage combine',
            'cov-report': 'coverage report',
        },
        'matrix': [{'python': ['3.13', '3.12', '3.11', '3.10', '3.9', '3.8']}],
    }
