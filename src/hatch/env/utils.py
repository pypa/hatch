from __future__ import annotations

import os

from hatch.config.constants import AppEnvVars


def get_env_var(*, plugin_name: str, option: str) -> str:
    return f"{AppEnvVars.ENV_OPTION_PREFIX}{plugin_name}_{option.replace('-', '_')}".upper()


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


def get_verbosity_flag(verbosity: int, *, adjustment=0) -> str:
    verbosity += adjustment
    if not verbosity:
        return ""

    if verbosity > 0:
        return f"-{'v' * abs(min(verbosity, 3))}"

    return f"-{'q' * abs(max(verbosity, -3))}"


def add_verbosity_flag(command: list[str], verbosity: int, *, adjustment=0):
    flag = get_verbosity_flag(verbosity, adjustment=adjustment)
    if flag:
        command.append(flag)
