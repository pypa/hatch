class ShellManager:
    def __init__(self, environment):
        self.environment = environment

    def enter_cmd(self, shell_path, exe_dir):
        self.environment.platform.exit_with_command([shell_path or 'cmd', '/k', str(exe_dir / 'activate.bat')])

    def enter_powershell(self, shell_path, exe_dir):
        self.environment.platform.exit_with_command(
            [
                shell_path or 'powershell',
                '-executionpolicy',
                'bypass',
                '-NoExit',
                '-NoLogo',
                '-File',
                str(exe_dir / 'activate.ps1'),
            ]
        )

    def enter_xonsh(self, shell_path, exe_dir):
        if self.environment.platform.windows:
            with self.environment:
                self.environment.platform.exit_with_command(
                    [shell_path or 'xonsh', '-i', '-D', f'VIRTUAL_ENV={exe_dir.parent.name}']
                )
        else:
            self.spawn_linux_shell(
                shell_path or 'xonsh',
                ['-i', '-D', f'VIRTUAL_ENV={exe_dir.parent.name}'],
                # Just in case pyenv works with xonsh, supersede it.
                callback=lambda terminal: terminal.sendline(f'$PATH.insert(0, {str(exe_dir)!r})'),
            )

    def enter_bash(self, shell_path, exe_dir):
        self.spawn_linux_shell(shell_path or 'bash', ['-i'], script=exe_dir / 'activate')

    def enter_fish(self, shell_path, exe_dir):
        self.spawn_linux_shell(shell_path or 'fish', ['-i'], script=exe_dir / 'activate.fish')

    def enter_zsh(self, shell_path, exe_dir):
        self.spawn_linux_shell(shell_path or 'zsh', ['-i'], script=exe_dir / 'activate')

    def enter_nu(self, shell_path, exe_dir):
        executable = shell_path or 'nu'
        activation_script = exe_dir / 'activate.nu'
        if self.environment.platform.windows:
            self.environment.platform.exit_with_command(
                [executable, '-c', f'source "{activation_script}"; "{executable}"']
            )
        else:
            self.spawn_linux_shell(executable, None, script=activation_script)

    def enter_tcsh(self, shell_path, exe_dir):
        self.spawn_linux_shell(shell_path or 'tcsh', ['-i'], script=exe_dir / 'activate.csh')

    def enter_csh(self, shell_path, exe_dir):
        self.spawn_linux_shell(shell_path or 'csh', ['-i'], script=exe_dir / 'activate.csh')

    def spawn_linux_shell(self, shell_path, args, *, script=None, callback=None):
        import shutil
        import signal

        import pexpect

        columns, lines = shutil.get_terminal_size()
        terminal = pexpect.spawn(shell_path, args=args, dimensions=(lines, columns))

        def sigwinch_passthrough(sig, data):
            terminal.setwinsize(lines, columns)

        signal.signal(signal.SIGWINCH, sigwinch_passthrough)

        if script is not None:
            terminal.sendline(f'source "{script}"')

        if callback is not None:
            callback(terminal)

        terminal.interact(escape_character=None)
        terminal.close()

        self.environment.platform.exit_with_code(terminal.exitstatus)
