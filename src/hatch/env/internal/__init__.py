from __future__ import annotations

from typing import Any

from hatch.env.utils import ensure_valid_environment


def get_internal_env_config() -> dict[str, Any]:
    from hatch.env.internal import build, static_analysis, test, uv

    internal_config = {}
    for env_name, env_config in (
        ('hatch-build', build.get_default_config()),
        ('hatch-static-analysis', static_analysis.get_default_config()),
        ('hatch-test', test.get_default_config()),
        ('hatch-uv', uv.get_default_config()),
    ):
        env_config['template'] = env_name
        ensure_valid_environment(env_config)
        internal_config[env_name] = env_config

    return internal_config


def is_isolated_environment(env_name: str, config: dict[str, Any]) -> bool:
    # Provide super isolation and immunity to project-level environment removal only when the environment:
    #
    # 1. Does not require the project being installed
    # 2. The default configuration is used
    #
    # For example, the environment for static analysis depends only on Ruff at a specific default
    # version. This environment does not require the project and can be reused by every project to
    # improve responsiveness. However, if the user for some reason chooses to override the dependencies
    # to use a different version of Ruff, then the project would get its own environment.
    return config.get('skip-install', False) and is_default_environment(env_name, config)


def is_default_environment(env_name: str, config: dict[str, Any]) -> bool:
    # Standalone environment
    internal_config = get_internal_env_config().get(env_name)
    if not internal_config:
        # Environment generated from matrix
        internal_config = get_internal_env_config().get(env_name.split('.')[0])
        if not internal_config:
            return False

    # Only consider things that would modify the actual installation, other options like extra scripts don't matter
    for key in ('dependencies', 'extra-dependencies', 'features'):
        if config.get(key) != internal_config.get(key):
            return False

    return True
