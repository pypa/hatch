class AppEnvVars:
    ENV: str = 'HATCH_ENV'
    ENV_ACTIVE: str = 'HATCH_ENV_ACTIVE'
    ENV_OPTION_PREFIX: str = 'HATCH_ENV_TYPE_'
    QUIET: str = 'HATCH_QUIET'
    VERBOSE: str = 'HATCH_VERBOSE'
    INTERACTIVE: str = 'HATCH_INTERACTIVE'
    PYTHON: str = 'HATCH_PYTHON'
    # https://no-color.org
    NO_COLOR: str = 'NO_COLOR'
    FORCE_COLOR: str = 'FORCE_COLOR'


class ConfigEnvVars:
    PROJECT: str = 'HATCH_PROJECT'
    DATA: str = 'HATCH_DATA_DIR'
    CACHE: str = 'HATCH_CACHE_DIR'
    CONFIG: str = 'HATCH_CONFIG'


class PublishEnvVars:
    USER: str = 'HATCH_INDEX_USER'
    AUTH: str = 'HATCH_INDEX_AUTH'
    REPO: str = 'HATCH_INDEX_REPO'
    CA_CERT: str = 'HATCH_INDEX_CA_CERT'
    CLIENT_CERT: str = 'HATCH_INDEX_CLIENT_CERT'
    CLIENT_KEY: str = 'HATCH_INDEX_CLIENT_KEY'
    PUBLISHER: str = 'HATCH_PUBLISHER'
    OPTIONS: str = 'HATCH_PUBLISHER_OPTIONS'
