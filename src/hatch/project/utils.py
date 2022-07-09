def format_script_commands(commands, ignore_exit_code, args):
    for command in commands:
        if args:
            command = f'{command} {args}'
        if ignore_exit_code and not command.startswith('- '):
            command = f'- {command}'

        yield command
