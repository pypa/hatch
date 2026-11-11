from __future__ import annotations

import os

from hatch.config.constants import AppEnvVars


def get_env_var(*, plugin_name: str, option: str) -> str:
    return f"{AppEnvVars.ENV_OPTION_PREFIX}{plugin_name.replace('-', '_')}_{option.replace('-', '_')}".upper()


def get_env_var_option(*, plugin_name: str, option: str, default: str = "") -> str:
    return os.environ.get(get_env_var(plugin_name=plugin_name, option=option), default)


def ensure_valid_environment(env_config: dict):
    env_config.setdefault("type", "virtual")

    workspace = env_config.get("workspace")
    if workspace is not None:
        if not isinstance(workspace, dict):
            msg = "Field workspace must be a table"
            raise TypeError(msg)

        members = workspace.get("members", [])
        if not isinstance(members, list):
            msg = "Field workspace.members must be an array"
            raise TypeError(msg)

        # Validate each member
        for i, member in enumerate(members, 1):
            if isinstance(member, str):
                continue
            if isinstance(member, dict):
                path = member.get("path")
                if path is None:
                    msg = f"Member #{i} must define a `path` key"
                    raise TypeError(msg)
                if not isinstance(path, str):
                    msg = f"Member #{i} path must be a string"
                    raise TypeError(msg)
            else:
                msg = f"Member #{i} must be a string or table"
                raise TypeError(msg)

        exclude = workspace.get("exclude", [])
        if not isinstance(exclude, list):
            msg = "Field workspace.exclude must be an array"
            raise TypeError(msg)


# Caps repeated `-v`/`-q` characters. Above the historical default of 3, and
# far below a size that could exhaust memory.
MAX_VERBOSITY_FLAG_LENGTH = 100


def get_verbosity_flag(verbosity: int, *, adjustment=0, maximum=3) -> str:
    if maximum < 0:
        message = f"Verbosity flag maximum must be a non-negative integer: {maximum}"
        raise ValueError(message)
    if maximum > MAX_VERBOSITY_FLAG_LENGTH:
        message = f"Verbosity flag maximum must be less than or equal to {MAX_VERBOSITY_FLAG_LENGTH}: {maximum}"
        raise ValueError(message)

    verbosity += adjustment
    if not verbosity or maximum == 0:
        return ""

    if verbosity > 0:
        return f"-{'v' * min(verbosity, maximum)}"

    return f"-{'q' * min(abs(verbosity), maximum)}"


def add_verbosity_flag(command: list[str], verbosity: int, *, adjustment=0, maximum=3):
    flag = get_verbosity_flag(verbosity, adjustment=adjustment, maximum=maximum)
    if flag:
        command.append(flag)
