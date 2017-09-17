import os
import pexpect
import shutil
import signal
import subprocess

from hatch.settings import load_settings
from hatch.utils import NEED_SUBPROCESS_SHELL, ON_WINDOWS, basepath

DEFAULT_SHELL = 'cmd' if ON_WINDOWS else 'bash'


def get_terminal_dimensions():
    columns, lines = shutil.get_terminal_size()
    return lines, columns


def cmd_shell(exe_dir, shell_path):
    result = subprocess.run(
        [shell_path or 'cmd', '/k', os.path.join(exe_dir, 'activate.bat')],
        shell=NEED_SUBPROCESS_SHELL
    )
    return result.returncode


def ps_shell(exe_dir, shell_path):
    result = subprocess.run(
        [shell_path or 'powershell', '-executionpolicy', 'bypass', '-NoExit',
         '-NoLogo', '-File', os.path.join(exe_dir, 'activate.ps1')],
        shell=NEED_SUBPROCESS_SHELL
    )
    return result.returncode


def bash_shell(exe_dir, shell_path):
    terminal = pexpect.spawn(
        shell_path or 'bash',
        args=['-i'],
        dimensions=get_terminal_dimensions()
    )

    def sigwinch_passthrough(sig, data):
        terminal.setwinsize(*get_terminal_dimensions())
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    terminal.sendline('source "{}"'.format(os.path.join(exe_dir, 'activate')))
    terminal.interact(escape_character=None)
    terminal.close()
    return terminal.exitstatus


def fish_shell(exe_dir, shell_path):
    terminal = pexpect.spawn(
        shell_path or 'fish',
        args=['-i'],
        dimensions=get_terminal_dimensions()
    )

    def sigwinch_passthrough(sig, data):
        terminal.setwinsize(*get_terminal_dimensions())
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    terminal.sendline('source "{}"'.format(os.path.join(exe_dir, 'activate.fish')))
    terminal.interact(escape_character=None)
    terminal.close()
    return terminal.exitstatus


def zsh_shell(exe_dir, shell_path):
    terminal = pexpect.spawn(
        shell_path or 'zsh',
        args=['-i'],
        dimensions=get_terminal_dimensions()
    )

    def sigwinch_passthrough(sig, data):
        terminal.setwinsize(*get_terminal_dimensions())
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    terminal.sendline('source "{}"'.format(os.path.join(exe_dir, 'activate')))
    terminal.interact(escape_character=None)
    terminal.close()
    return terminal.exitstatus


def xonsh_shell(exe_dir, shell_path):
    if ON_WINDOWS:
        result = subprocess.run(
            [shell_path or 'xonsh', '-i', '-D',
             'VIRTUAL_ENV={}'.format(os.path.dirname(exe_dir))],
            shell=NEED_SUBPROCESS_SHELL
        )
        return result.returncode
    else:
        terminal = pexpect.spawn(
            shell_path or 'xonsh',
            args=['-i', '-D', 'VIRTUAL_ENV={}'.format(os.path.dirname(exe_dir))],
            dimensions=get_terminal_dimensions()
        )

        def sigwinch_passthrough(sig, data):
            terminal.setwinsize(*get_terminal_dimensions())
        signal.signal(signal.SIGWINCH, sigwinch_passthrough)

        # Just in case pyenv works with xonsh, supersede it.
        terminal.sendline('$PATH.insert(0, "{}")'.format(exe_dir))

        terminal.interact(escape_character=None)
        terminal.close()
        return terminal.exitstatus


def tcsh_shell(exe_dir, shell_path):
    terminal = pexpect.spawn(
        shell_path or 'tcsh',
        args=['-i'],
        dimensions=get_terminal_dimensions()
    )

    def sigwinch_passthrough(sig, data):
        terminal.setwinsize(*get_terminal_dimensions())
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    terminal.sendline('source "{}"'.format(os.path.join(exe_dir, 'activate.csh')))
    terminal.interact(escape_character=None)
    terminal.close()
    return terminal.exitstatus


def csh_shell(exe_dir, shell_path):
    terminal = pexpect.spawn(
        shell_path or 'csh',
        args=['-i'],
        dimensions=get_terminal_dimensions()
    )

    def sigwinch_passthrough(sig, data):
        terminal.setwinsize(*get_terminal_dimensions())
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    terminal.sendline('source "{}"'.format(os.path.join(exe_dir, 'activate.csh')))
    terminal.interact(escape_character=None)
    terminal.close()
    return terminal.exitstatus


def unknown_shell(shell_name):
    result = subprocess.run(shell_name.split(), shell=NEED_SUBPROCESS_SHELL)
    return result.returncode


SHELL_COMMANDS = {
    'cmd': cmd_shell,
    'powershell': ps_shell,
    'ps': ps_shell,
    'bash': bash_shell,
    'fish': fish_shell,
    'zsh': zsh_shell,
    'xonsh': xonsh_shell,
    'tcsh': tcsh_shell,
    'csh': csh_shell,
}


def get_default_shell_info(shell_name=None, settings=None):
    if not shell_name:
        settings = settings or load_settings(lazy=True)

        shell_name = settings.get('shell')
        if shell_name:
            return shell_name, None

        shell_path = os.environ.get('SHELL')
        if shell_path:
            shell_name = basepath(shell_path)
        else:
            shell_name = DEFAULT_SHELL

        return shell_name, shell_path

    return shell_name, None


def run_shell(exe_dir, shell_name=None):
    shell_name, shell_path = get_default_shell_info(shell_name)
    shell = SHELL_COMMANDS.get(shell_name)
    return shell(exe_dir, shell_path) if shell else unknown_shell(shell_name)
