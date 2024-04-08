from __future__ import annotations

from typing import Any, Iterable


def parse_script_command(command: str) -> tuple[str, str, bool]:
    possible_script, _, args = command.partition(' ')
    if possible_script == '-':
        ignore_exit_code = True
        possible_script, _, args = args.partition(' ')
    else:
        ignore_exit_code = False

    return possible_script, args, ignore_exit_code


def format_script_commands(*, commands: list[str], args: str, ignore_exit_code: bool) -> Iterable[str]:
    for command in commands:
        if args:
            yield f'{command} {args}'
        elif ignore_exit_code and not command.startswith('- '):
            yield f'- {command}'
        else:
            yield command


def parse_inline_script_metadata(script: str) -> dict[str, Any] | None:
    """
    https://peps.python.org/pep-0723/#reference-implementation
    """
    import re

    from hatch.utils.toml import load_toml_data

    block_type = 'script'
    pattern = re.compile(r'(?m)^# /// (?P<type>[a-zA-Z0-9-]+)$\s(?P<content>(^#(| .*)$\s)+)^# ///$')
    matches = list(filter(lambda m: m.group('type') == block_type, pattern.finditer(script)))
    if len(matches) > 1:
        message = f'Multiple inline metadata blocks found for type: {block_type}'
        raise ValueError(message)

    if len(matches) == 1:
        content = ''.join(
            line[2:] if line.startswith('# ') else line[1:]
            for line in matches[0].group('content').splitlines(keepends=True)
        )
        return load_toml_data(content)

    return None
