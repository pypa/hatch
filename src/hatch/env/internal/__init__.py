from __future__ import annotations

import os
import shutil
import sysconfig
from functools import cache
from typing import Any

from hatch.env.utils import ensure_valid_environment


@cache
def uv_available() -> bool:
    # `uv` is an optional dependency, so detect whether it is actually installed before defaulting
    # the internal environments to it. This mirrors the standalone detection used by the virtual
    # environment type (see `hatch.env.virtual.VirtualEnvironment.uv_path`): when `uv` is installed
    # as a Python package it lands in the install environment's scripts directory, which is not
    # necessarily on the running process's `PATH`, so that directory is prepended before searching.
    #
    # The result is cached because `default_installer` is called by every internal environment config
    # producer, and a fresh `PATH` scan on every config build is wasteful. Tests that toggle `uv`
    # availability must clear this cache (`uv_available.cache_clear()`).
    scripts_dir = sysconfig.get_path("scripts")
    old_path = os.environ.get("PATH", os.defpath)
    new_path = f"{scripts_dir}{os.pathsep}{old_path}"
    return shutil.which("uv", path=new_path) is not None


def default_installer() -> str:
    return "uv" if uv_available() else "pip"


def get_internal_env_config() -> dict[str, Any]:
    from hatch.env.internal import build, static_analysis, test, type_check, uv

    internal_config = {}
    for env_name, env_config in (
        ("hatch-build", build.get_default_config()),
        ("hatch-check-code", static_analysis.get_check_code_config()),
        ("hatch-check-fmt", static_analysis.get_check_fmt_config()),
        ("hatch-check-types", type_check.get_default_config()),
        ("hatch-static-analysis", static_analysis.get_default_config()),
        ("hatch-test", test.get_default_config()),
        ("hatch-uv", uv.get_default_config()),
    ):
        env_config["template"] = env_name
        ensure_valid_environment(env_config)
        internal_config[env_name] = env_config

    return internal_config


def is_isolated_environment(env_name: str, config: dict[str, Any]) -> bool:
    # Provide super isolation and immunity to project-level environment removal only when the environment:
    #
    # 1. Is not used for builds
    # 2. Does not require the project being installed
    # 3. The default configuration is used
    #
    # For example, the environment for static analysis depends only on Ruff at a specific default
    # version. This environment does not require the project and can be reused by every project to
    # improve responsiveness. However, if the user for some reason chooses to override the dependencies
    # to use a different version of Ruff, then the project would get its own environment.
    return (
        not config.get("builder", False)
        and config.get("skip-install", False)
        and is_default_environment(env_name, config)
    )


def is_default_environment(env_name: str, config: dict[str, Any]) -> bool:
    # Standalone environment
    internal_config = get_internal_env_config().get(env_name)
    if not internal_config:
        # Environment generated from matrix
        internal_config = get_internal_env_config().get(env_name.split(".")[0])
        if not internal_config:
            return False

    # Only consider things that would modify the actual installation, other options like extra scripts don't matter
    for key in ("dependencies", "extra-dependencies", "features"):
        if config.get(key) != internal_config.get(key):
            return False

    return True
