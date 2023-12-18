from __future__ import annotations


def get_default_config() -> dict:
    return {
        'skip-install': True,
        'dependencies': ['build[virtualenv]>=1.0.3'],
        'scripts': {
            'build-all': 'python -m build',
            'build-sdist': 'python -m build --sdist',
            'build-wheel': 'python -m build --wheel',
        },
    }
