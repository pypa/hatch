from __future__ import annotations

import json
import os
import platform
import sys
from functools import lru_cache
from typing import Any

from hatch._version import __version__


def get_linehaul_data() -> dict[str, Any]:
    data: dict[str, Any] = {
        "installer": {"name": "hatch", "version": __version__},
        "python": platform.python_version(),
        "implementation": {
            "name": platform.python_implementation(),
            "version": _get_implementation_version(),
        },
        "system": {
            "name": platform.system(),
            "release": platform.release(),
        },
        "cpu": platform.machine(),
        "ci": _looks_like_ci() or None,
    }

    if sys.platform.startswith("linux"):
        distro_info = _get_linux_distro_info()
        if distro_info:
            data["distro"] = distro_info
    elif sys.platform == "darwin":
        mac_version = platform.mac_ver()[0]
        if mac_version:
            data["distro"] = {"name": "macOS", "version": mac_version}

    openssl_version = _get_openssl_version()
    if openssl_version:
        data["openssl_version"] = openssl_version

    return data


def _get_implementation_version() -> str:
    implementation_name = platform.python_implementation()

    if implementation_name == "PyPy":
        pypy_version_info = sys.pypy_version_info  # type: ignore[attr-defined]
        if pypy_version_info.releaselevel == "final":
            pypy_version_info = pypy_version_info[:3]
        return ".".join(str(x) for x in pypy_version_info)

    return platform.python_version()


def _get_linux_distro_info() -> dict[str, Any] | None:
    import distro

    name = distro.name()
    if not name:
        return None

    distro_info: dict[str, Any] = {"name": name}

    version = distro.version()
    if version:
        distro_info["version"] = version

    codename = distro.codename()
    if codename:
        distro_info["id"] = codename

    libc_info = _get_libc_info()
    if libc_info:
        distro_info["libc"] = libc_info

    return distro_info


def _get_libc_info() -> dict[str, str] | None:
    libc, version = _get_libc_version()
    if libc and version:
        return {"lib": libc, "version": version}
    return None


def _get_libc_version() -> tuple[str | None, str | None]:
    import ctypes
    import ctypes.util

    libc_name = ctypes.util.find_library("c")
    if not libc_name:
        return None, None

    try:
        libc = ctypes.CDLL(libc_name)
        libc.gnu_get_libc_version.restype = ctypes.c_char_p
        version = libc.gnu_get_libc_version()
        if version:
            return "glibc", version.decode()
    except (OSError, AttributeError, UnicodeDecodeError):
        pass

    return None, None


def _get_openssl_version() -> str | None:
    try:
        import ssl
    except (ImportError, AttributeError):
        return None
    else:
        return ssl.OPENSSL_VERSION


def _looks_like_ci() -> bool:
    # INFO: Matches pip's CI detection for linehaul statistics.
    # Uses existence check (not value check) because variables like BUILD_BUILDID
    # and BUILD_ID are set to build IDs, not boolean strings.
    ci_env_vars = (
        "BUILD_BUILDID",
        "BUILD_ID",
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "PIP_IS_CI",
        "TRAVIS",
    )
    return any(env_var in os.environ for env_var in ci_env_vars)


@lru_cache(maxsize=1)
def get_linehaul_component() -> str:
    data = get_linehaul_data()
    return json.dumps(data, separators=(",", ":"), sort_keys=True)
