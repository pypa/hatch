from typing import ClassVar


class AppEnvVars:
    ENV: ClassVar[str] = 'HATCH_ENV'
    ENV_ACTIVE: ClassVar[str] = 'HATCH_ENV_ACTIVE'
    ENV_OPTION_PREFIX: ClassVar[str] = 'HATCH_ENV_TYPE_'
    QUIET: ClassVar[str] = 'HATCH_QUIET'
    VERBOSE: ClassVar[str] = 'HATCH_VERBOSE'
    INTERACTIVE: ClassVar[str] = 'HATCH_INTERACTIVE'
    PYTHON: ClassVar[str] = 'HATCH_PYTHON'
    # https://no-color.org
    NO_COLOR: ClassVar[str] = 'NO_COLOR'
    FORCE_COLOR: ClassVar[str] = 'FORCE_COLOR'


class ConfigEnvVars:
    PROJECT: ClassVar[str] = 'HATCH_PROJECT'
    DATA: ClassVar[str] = 'HATCH_DATA_DIR'
    CACHE: ClassVar[str] = 'HATCH_CACHE_DIR'
    CONFIG: ClassVar[str] = 'HATCH_CONFIG'


class PublishEnvVars:
    USER: ClassVar[str] = 'HATCH_INDEX_USER'
    AUTH: ClassVar[str] = 'HATCH_INDEX_AUTH'
    REPO: ClassVar[str] = 'HATCH_INDEX_REPO'
    CA_CERT: ClassVar[str] = 'HATCH_INDEX_CA_CERT'
    CLIENT_CERT: ClassVar[str] = 'HATCH_INDEX_CLIENT_CERT'
    CLIENT_KEY: ClassVar[str] = 'HATCH_INDEX_CLIENT_KEY'
    PUBLISHER: ClassVar[str] = 'HATCH_PUBLISHER'
    OPTIONS: ClassVar[str] = 'HATCH_PUBLISHER_OPTIONS'
