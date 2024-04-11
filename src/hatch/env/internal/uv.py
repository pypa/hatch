from __future__ import annotations


def get_default_config() -> dict:
    return {
        'skip-install': True,
        'dependencies': ['uv==0.1.31'],
    }
