from __future__ import annotations

from collections.abc import Iterator


def parse_script_command(command: str) -> tuple[str, str, bool]:
    possible_script, _, args = command.partition(' ')
    if possible_script == '-':
        ignore_exit_code = True
        possible_script, _, args = args.partition(' ')
    else:
        ignore_exit_code = False

    return possible_script, args, ignore_exit_code


def format_script_commands(commands: list[str], args: str, ignore_exit_code: bool) -> Iterator[str]:
    for command in commands:
        if args:
            command = f'{command} {args}'
        if ignore_exit_code and not command.startswith('- '):
            command = f'- {command}'

        yield command
