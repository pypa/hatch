from __future__ import annotations


def ensure_valid_environment(env_config: dict):
    env_config.setdefault('type', 'virtual')


def get_verbosity_flag(verbosity: int, *, adjustment=0) -> str:
    verbosity += adjustment
    if not verbosity:
        return ''
    elif verbosity > 0:
        return f'-{"v" * abs(min(verbosity, 3))}'
    else:
        return f'-{"q" * abs(max(verbosity, -3))}'


def add_verbosity_flag(command: list[str], verbosity: int, *, adjustment=0):
    flag = get_verbosity_flag(verbosity, adjustment=adjustment)
    if flag:
        command.append(flag)
