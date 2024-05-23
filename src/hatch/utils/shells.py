from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from hatch.utils.fs import Path

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from types import FrameType

    from hatch.env.plugin.interface import EnvironmentInterface
    from hatch.utils.platform import Platform


def detect_shell(platform: Platform) -> tuple[str, str]:
    import shellingham

    try:
        return shellingham.detect_shell()
    except shellingham.ShellDetectionFailure:
        path = platform.default_shell
        return Path(path).stem, path


class ShellManager:
    def __init__(self, environment: EnvironmentInterface) -> None:
        self.environment = environment

    def enter_cmd(self, path: str, args: Iterable[str], exe_dir: Path) -> None:  # noqa: ARG002
        self.environment.platform.exit_with_command([path or 'cmd', '/k', str(exe_dir / 'activate.bat')])

    def enter_powershell(self, path: str, args: Iterable[str], exe_dir: Path) -> None:  # noqa: ARG002
        self.environment.platform.exit_with_command([
            path or 'powershell',
            '-executionpolicy',
            'bypass',
            '-NoExit',
            '-NoLogo',
            '-File',
            str(exe_dir / 'activate.ps1'),
        ])

    def enter_pwsh(self, path: str, args: Iterable[str], exe_dir: Path) -> None:
        self.enter_powershell(path or 'pwsh', args, exe_dir)

    def enter_xonsh(self, path: str, args: Iterable[str], exe_dir: Path) -> None:
        if self.environment.platform.windows:
            with self.environment:
                self.environment.platform.exit_with_command([
                    path or 'xonsh',
                    *(args or ['-i']),
                    '-D',
                    f'VIRTUAL_ENV={exe_dir.parent.name}',
                ])
        else:
            self.spawn_linux_shell(
                path or 'xonsh',
                [*(args or ['-i']), '-D', f'VIRTUAL_ENV={exe_dir.parent.name}'],
                # Just in case pyenv works with xonsh, supersede it.
                callback=lambda terminal: terminal.sendline(f'$PATH.insert(0, {str(exe_dir)!r})'),
            )

    def enter_bash(self, path: str, args: Iterable[str], exe_dir: Path) -> None:
        if self.environment.platform.windows:
            self.environment.platform.exit_with_command([
                path or 'bash',
                '--init-file',
                exe_dir / 'activate',
                *(args or ['-i']),
            ])
        else:
            self.spawn_linux_shell(path or 'bash', args or ['-i'], script=exe_dir / 'activate')

    def enter_fish(self, path: str, args: Iterable[str], exe_dir: Path) -> None:
        self.spawn_linux_shell(path or 'fish', args or ['-i'], script=exe_dir / 'activate.fish')

    def enter_zsh(self, path: str, args: Iterable[str], exe_dir: Path) -> None:
        self.spawn_linux_shell(path or 'zsh', args or ['-i'], script=exe_dir / 'activate')

    def enter_ash(self, path: str, args: Iterable[str], exe_dir: Path) -> None:
        self.spawn_linux_shell(path or 'ash', args or ['-i'], script=exe_dir / 'activate')

    def enter_nu(self, path: str, args: Iterable[str], exe_dir: Path) -> None:  # noqa: ARG002
        executable = path or 'nu'
        activation_script = exe_dir / 'activate.nu'
        self.environment.platform.exit_with_command([executable, '-e', f'overlay use {str(activation_script)!r}'])

    def enter_tcsh(self, path: str, args: Iterable[str], exe_dir: Path) -> None:
        self.spawn_linux_shell(path or 'tcsh', args or ['-i'], script=exe_dir / 'activate.csh')

    def enter_csh(self, path: str, args: Iterable[str], exe_dir: Path) -> None:
        self.spawn_linux_shell(path or 'csh', args or ['-i'], script=exe_dir / 'activate.csh')

    if sys.platform == 'win32':

        def spawn_linux_shell(
            self,
            path: str,
            args: Iterable[str] | None = None,
            *,
            script: Path | None = None,
            callback: Callable | None = None,
        ) -> None:
            raise NotImplementedError

    else:

        def spawn_linux_shell(
            self,
            path: str,
            args: Iterable[str] | None = None,
            *,
            script: Path | None = None,
            callback: Callable | None = None,
        ) -> None:
            import shutil
            import signal

            import pexpect

            columns, lines = shutil.get_terminal_size()
            # pexpect only accepts lists
            terminal = pexpect.spawn(path, args=list(args or ()), dimensions=(lines, columns))

            def sigwinch_passthrough(sig: int, data: FrameType | None) -> None:  # noqa: ARG001
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
