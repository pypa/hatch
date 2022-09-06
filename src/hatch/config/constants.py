from dataclasses import dataclass


@dataclass(frozen=True)
class AppEnvVarsCls:
    ENV = 'HATCH_ENV'
    ENV_ACTIVE = 'HATCH_ENV_ACTIVE'
    ENV_OPTION_PREFIX = 'HATCH_ENV_TYPE_'
    QUIET = 'HATCH_QUIET'
    VERBOSE = 'HATCH_VERBOSE'
    INTERACTIVE = 'HATCH_INTERACTIVE'
    PYTHON = 'HATCH_PYTHON'
    # https://no-color.org
    NO_COLOR = 'NO_COLOR'
    FORCE_COLOR = 'FORCE_COLOR'


AppEnvVars = AppEnvVarsCls()


@dataclass(frozen=True)
class ConfigEnvVarsCls:
    PROJECT = 'HATCH_PROJECT'
    DATA = 'HATCH_DATA_DIR'
    CACHE = 'HATCH_CACHE_DIR'
    CONFIG = 'HATCH_CONFIG'


ConfigEnvVars = ConfigEnvVarsCls()


@dataclass(frozen=True)
class PublishEnvVarsCls:
    USER = 'HATCH_INDEX_USER'
    AUTH = 'HATCH_INDEX_AUTH'
    REPO = 'HATCH_INDEX_REPO'
    CA_CERT = 'HATCH_INDEX_CA_CERT'
    CLIENT_CERT = 'HATCH_INDEX_CLIENT_CERT'
    CLIENT_KEY = 'HATCH_INDEX_CLIENT_KEY'
    PUBLISHER = 'HATCH_PUBLISHER'
    OPTIONS = 'HATCH_PUBLISHER_OPTIONS'


PublishEnvVars = PublishEnvVarsCls()
