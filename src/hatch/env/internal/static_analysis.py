from __future__ import annotations


def get_default_config() -> dict:
    return {
        'skip-install': True,
        'dependencies': [f'ruff=={RUFF_DEFAULT_VERSION}'],
    }


RUFF_DEFAULT_VERSION: str = '0.1.8'
