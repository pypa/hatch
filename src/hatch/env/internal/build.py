from __future__ import annotations

from hatch.env.internal.interface import InternalEnvironment


class InternalBuildEnvironment(InternalEnvironment):
    def get_base_config(self) -> dict:
        return {
            'skip-install': True,
            'dependencies': ['build[virtualenv]>=1.0.3'],
            'scripts': {
                'build-all': 'python -m build',
                'build-sdist': 'python -m build --sdist',
                'build-wheel': 'python -m build --wheel',
            },
        }
