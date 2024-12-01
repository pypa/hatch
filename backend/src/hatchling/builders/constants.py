DEFAULT_BUILD_DIRECTORY = 'dist'

EXCLUDED_DIRECTORIES = frozenset((
    # Python bytecode
    '__pycache__',
    # Single virtual environment
    '.venv',
    # Git
    '.git',
    # Mercurial
    '.hg',
    # Hatch
    '.hatch',
    # tox
    '.tox',
    # nox
    '.nox',
    # Ruff
    '.ruff_cache',
    # pytest
    '.pytest_cache',
    # Mypy
    '.mypy_cache',
    # pixi
    '.pixi',
))
EXCLUDED_FILES = frozenset((
    # https://en.wikipedia.org/wiki/.DS_Store
    '.DS_Store',
))


class BuildEnvVars:
    LOCATION = 'HATCH_BUILD_LOCATION'
    HOOKS_ONLY = 'HATCH_BUILD_HOOKS_ONLY'
    NO_HOOKS = 'HATCH_BUILD_NO_HOOKS'
    HOOKS_ENABLE = 'HATCH_BUILD_HOOKS_ENABLE'
    HOOK_ENABLE_PREFIX = 'HATCH_BUILD_HOOK_ENABLE_'
    CLEAN = 'HATCH_BUILD_CLEAN'
    CLEAN_HOOKS_AFTER = 'HATCH_BUILD_CLEAN_HOOKS_AFTER'


EDITABLES_REQUIREMENT = 'editables~=0.3'
