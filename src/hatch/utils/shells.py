class ShellManager:
    def __init__(self, environment):
        self.environment = environment

    def enter_cmd(self, path, args, exe_dir):
        self.environment.platform.exit_with_command([path or 'cmd', '/k', str(exe_dir / 'activate.bat')])

    def enter_powershell(self, path, args, exe_dir):
        self.environment.platform.exit_with_command(
            [
                path or 'powershell',
                '-executionpolicy',
                'bypass',
                '-NoExit',
                '-NoLogo',
                '-File',
                str(exe_dir / 'activate.ps1'),
            ]
        )

    def enter_pwsh(self, path, args, exe_dir):
        self.enter_powershell(path or 'pwsh', args, exe_dir)

    def enter_xonsh(self, path, args, exe_dir):
        if self.environment.platform.windows:
            with self.environment:
                self.environment.platform.exit_with_command(
                    [path or 'xonsh', *(args or ['-i']), '-D', f'VIRTUAL_ENV={exe_dir.parent.name}']
                )
        else:
            self.spawn_linux_shell(
                path or 'xonsh',
                [*(args or ['-i']), '-D', f'VIRTUAL_ENV={exe_dir.parent.name}'],
                # Just in case pyenv works with xonsh, supersede it.
                callback=lambda terminal: terminal.sendline(f'$PATH.insert(0, {str(exe_dir)!r})'),
            )

    def enter_bash(self, path, args, exe_dir):
        if self.environment.platform.windows:
            self.environment.platform.exit_with_command(
                [path or 'bash', '--init-file', exe_dir / 'activate', *(args or ['-i'])]
            )
        else:
            self.spawn_linux_shell(path or 'bash', args or ['-i'], script=exe_dir / 'activate')

    def enter_fish(self, path, args, exe_dir):
        self.spawn_linux_shell(path or 'fish', args or ['-i'], script=exe_dir / 'activate.fish')

    def enter_zsh(self, path, args, exe_dir):
        self.spawn_linux_shell(path or 'zsh', args or ['-i'], script=exe_dir / 'activate')

    def enter_ash(self, path, args, exe_dir):
        self.spawn_linux_shell(path or 'ash', args or ['-i'], script=exe_dir / 'activate')

    def enter_nu(self, path, args, exe_dir):
        executable = path or 'nu'
        activation_script = exe_dir / 'activate.nu'
        if self.environment.platform.windows:
            self.environment.platform.exit_with_command(
                [executable, '-c', f'source "{activation_script}"; "{executable}"']
            )
        else:
            self.spawn_linux_shell(executable, args or None, script=activation_script)

    def enter_tcsh(self, path, args, exe_dir):
        self.spawn_linux_shell(path or 'tcsh', args or ['-i'], script=exe_dir / 'activate.csh')

    def enter_csh(self, path, args, exe_dir):
        self.spawn_linux_shell(path or 'csh', args or ['-i'], script=exe_dir / 'activate.csh')

    def spawn_linux_shell(self, path, args, *, script=None, callback=None):
        import shutil
        import signal

        import pexpect

        columns, lines = shutil.get_terminal_size()
        terminal = pexpect.spawn(path, args=args, dimensions=(lines, columns))

        def sigwinch_passthrough(sig, data):
            new_columns, new_lines = shutil.get_terminal_size()
            terminal.setwinsize(new_lines, new_columns)

        signal.signal(signal.SIGWINCH, sigwinch_passthrough)

        if script is not None:
            terminal.sendline(f'source "{script}"')

        if callback is not None:
            callback(terminal)

        terminal.interact(escape_character=None)
        terminal.close()

        self.environment.platform.exit_with_code(terminal.exitstatus)
