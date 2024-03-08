from __future__ import annotations


def get_default_config() -> dict:
    return {
        'skip-install': True,
        'dependencies': [f'ruff=={RUFF_DEFAULT_VERSION}'],
        'scripts': {
            'format-check': 'ruff format{env:HATCH_FMT_ARGS} --check --diff {args:.}',
            'format-fix': 'ruff format{env:HATCH_FMT_ARGS} {args:.}',
            'lint-check': 'ruff check{env:HATCH_FMT_ARGS} {args:.}',
            'lint-fix': 'ruff check{env:HATCH_FMT_ARGS} --fix {args:.}',
        },
    }


RUFF_DEFAULT_VERSION: str = '0.3.1'
