DEFAULT_BUILD_DIRECTORY = 'dist'

EXCLUDED_DIRECTORIES = frozenset(
    (
        # Python bytecode
        '__pycache__',
        # PEP 582
        '__pypackages__',
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
    )
)


class BuildEnvVars:
    LOCATION = 'HATCH_BUILD_LOCATION'
    HOOKS_ONLY = 'HATCH_BUILD_HOOKS_ONLY'
    NO_HOOKS = 'HATCH_BUILD_NO_HOOKS'
    HOOKS_ENABLE = 'HATCH_BUILD_HOOKS_ENABLE'
    HOOK_ENABLE_PREFIX = 'HATCH_BUILD_HOOK_ENABLE_'
    CLEAN = 'HATCH_BUILD_CLEAN'
    CLEAN_HOOKS_AFTER = 'HATCH_BUILD_CLEAN_HOOKS_AFTER'
