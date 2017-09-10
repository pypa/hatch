import getpass
import os
import platform
import re
import subprocess
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from hatch.settings import load_settings
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, ON_WINDOWS, basepath, env_vars, temp_move_path
)

DEFAULT_SHELL = 'cmd' if ON_WINDOWS else 'bash'
VENV_TEXT = re.compile(r'^([0-9]+ )?\(([^)]+)\) ')


def get_prompt(command, default=''):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=NEED_SUBPROCESS_SHELL
    )
    if result.returncode == 0:
        output = b''
        output += result.stdout or b''
        output += result.stderr or b''
        if output:
            return output.decode().strip() + ' '
    return default


@contextmanager
def cmd_shell(env_name, nest, shell_path):
    old_prompt = os.environ.get('PROMPT', '$P$G')
    new_prompt = '({}) {}'.format(env_name, old_prompt)

    if nest:
        if VENV_TEXT.match(old_prompt):
            new_prompt = VENV_TEXT.sub('({}) '.format(env_name), old_prompt)

        hatch_level = int(os.environ.get('_HATCH_LEVEL_', 1))
        if hatch_level > 1:
            new_prompt = '{} {}'.format(hatch_level, new_prompt)

    with env_vars({'PROMPT': new_prompt}):
        yield [shell_path or 'cmd', '/k']


@contextmanager
def bash_shell(env_name, nest, shell_path):
    old_prompt = os.environ.get(
        'PS1',
        get_prompt([shell_path or 'bash', '-i', '-c', 'echo $PS1'])
    )
    new_prompt = '({}) {}'.format(env_name, old_prompt)

    if nest:
        if VENV_TEXT.match(old_prompt):
            new_prompt = VENV_TEXT.sub('({}) '.format(env_name), old_prompt)

        hatch_level = int(os.environ.get('_HATCH_LEVEL_', 1))
        if hatch_level > 1:
            new_prompt = '{} {}'.format(hatch_level, new_prompt)

    with TemporaryDirectory() as d:
        init_file = os.path.join(d, 'init_file')
        with open(init_file, 'w') as f:
            f.write(
                'source ~/.bashrc\n'
                'PS1="{}"\n'
                ''.format(new_prompt)
            )
        yield [shell_path or 'bash', '--init-file', init_file]


@contextmanager
def fish_shell(env_name, nest, shell_path):
    host = platform.node()
    try:
        user = getpass.getuser()
    except:
        user = os.getlogin()

    old_prompt = os.environ.get(
        'PS1',
        get_prompt(
            [shell_path or 'fish', '-i', '-c', 'fish_prompt'],
            default='[{}@{} \x1b[32m~\x1b[30m\x1b(B\x1b[m]$ '.format(user, host)
        )
    )
    new_prompt = '({}) {}'.format(env_name, old_prompt)

    if nest:
        if VENV_TEXT.match(old_prompt):
            new_prompt = VENV_TEXT.sub('({}) '.format(env_name), old_prompt)

        hatch_level = int(os.environ.get('_HATCH_LEVEL_', 1))
        if hatch_level > 1:
            new_prompt = '{} {}'.format(hatch_level, new_prompt)

    with TemporaryDirectory() as d:
        config_path = os.path.expanduser('~/.config/fish/config.fish')
        with temp_move_path(config_path, d) as path:
            new_config = ''
            if path:
                with open(path, 'r') as f:
                    new_config += f.read()

            new_config += (
                '\n'
                'function fish_prompt\n'
                '    echo {}\n'
                'end\n'.format(new_prompt)
            )

            with open(config_path, 'w') as f:
                f.write(new_config)
            yield [shell_path or 'fish']


@contextmanager
def zsh_shell(env_name, nest, shell_path):
    old_prompt = os.environ.get(
        'PROMPT',
        get_prompt([shell_path or 'zsh', '-i', '-c', 'echo $PROMPT'], default='%m%# ')
    )
    new_prompt = '({}) {}'.format(env_name, old_prompt)

    if nest:
        if VENV_TEXT.match(old_prompt):
            new_prompt = VENV_TEXT.sub('({}) '.format(env_name), old_prompt)

        hatch_level = int(os.environ.get('_HATCH_LEVEL_', 1))
        if hatch_level > 1:
            new_prompt = '{} {}'.format(hatch_level, new_prompt)

    with env_vars({'PROMPT': new_prompt}):
        yield [shell_path or 'zsh']


@contextmanager
def xonsh_shell(env_name, nest, shell_path):
    with TemporaryDirectory() as d:
        with temp_move_path(os.path.expanduser('~/.xonshrc'), d) as path:
            new_config = ''
            if path:
                with open(path, 'r') as f:
                    new_config += f.read()

            hatch_level = int(os.environ.get('_HATCH_LEVEL_', 1))

            if nest and hatch_level > 1:
                new_config += (
                    '\n$PROMPT_FIELDS["env_name"] = "{hatch_level} ({env_name})"\n'
                    ''.format(hatch_level=hatch_level, env_name=env_name)
                )
            else:
                new_config += (
                    '\n$PROMPT_FIELDS["env_name"] = "({env_name})"\n'
                    ''.format(env_name=env_name)
                )

            new_config_path = os.path.join(d, 'new.xonshrc')
            with open(new_config_path, 'w') as f:
                f.write(new_config)
            yield [shell_path or 'xonsh', '--rc', new_config_path]


@contextmanager
def unknown_shell(shell_name):
    # Assume it's a command and prepare it for Popen.
    yield shell_name.split()


SHELL_COMMANDS = {
    'cmd': cmd_shell,
    'bash': bash_shell,
    'fish': fish_shell,
    'zsh': zsh_shell,
    'xonsh': xonsh_shell,
}
IMMORTAL_SHELLS = {
    'fish',
    'zsh',
    'xonsh',
}


def get_default_shell_info(shell_name=None, settings=None):
    if not shell_name:
        try:
            settings = settings or load_settings()
        except FileNotFoundError:
            settings = {}

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


def get_shell_command(env_name, shell_name=None, shell_path=None, nest=False):
    shell = SHELL_COMMANDS.get(shell_name)
    return shell(env_name, nest, shell_path) if shell else unknown_shell(shell_name)
