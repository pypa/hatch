from __future__ import annotations

from typing import Any

from hatch.env.utils import ensure_valid_environment


def get_internal_env_config() -> dict[str, Any]:
    from hatch.env.internal import build, static_analysis

    internal_config = {}
    for env_name, env_config in (
        ('hatch-build', build.get_default_config()),
        ('hatch-static-analysis', static_analysis.get_default_config()),
    ):
        env_config['template'] = env_name
        ensure_valid_environment(env_config)
        internal_config[env_name] = env_config

    return internal_config
