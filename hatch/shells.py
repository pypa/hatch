import os
import re
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from hatch.utils import NEED_SUBPROCESS_SHELL, env_vars, temp_move_path

DEFAULT_SHELL = 'cmd' if NEED_SUBPROCESS_SHELL else 'bash'
VENV_TEXT = re.compile(r'^([0-9]+ )?\(([^)]+)\) ')


@contextmanager
def cmd_shell(env_name, nest):
    old_prompt = os.environ.get('PROMPT', '$P$G')
    new_prompt = '({}) {}'.format(env_name, old_prompt)

    if nest:
        if VENV_TEXT.match(old_prompt):
            new_prompt = VENV_TEXT.sub('({}) '.format(env_name), old_prompt)

        hatch_level = int(os.environ.get('_HATCH_LEVEL_', 1))
        if hatch_level > 1:
            new_prompt = '{} {}'.format(hatch_level, new_prompt)

    with env_vars({'PROMPT': new_prompt}):
        yield ['cmd', '/k']


@contextmanager
def bash_shell(env_name):
    with TemporaryDirectory() as d:
        init_file = os.path.join(d, 'init_file')
        with open(init_file, 'w') as f:
            f.write(
                'source ~/.bashrc\n'
                'PS1="({}) $PS1"\n'
                ''.format(env_name)
            )
        yield ['bash', '--init-file', init_file]


@contextmanager
def zsh_shell(env_name, nest):
    old_prompt = os.environ.get('PROMPT', '%m%# ')
    new_prompt = '({}) {}'.format(env_name, old_prompt)

    if nest:
        if VENV_TEXT.match(old_prompt):
            new_prompt = VENV_TEXT.sub('({}) '.format(env_name), old_prompt)

        hatch_level = int(os.environ.get('_HATCH_LEVEL_', 1))
        if hatch_level > 1:
            new_prompt = '{} {}'.format(hatch_level, new_prompt)

    with env_vars({'PROMPT': new_prompt}):
        yield ['zsh']


@contextmanager
def xonsh_shell(env_name):
    with TemporaryDirectory() as d:
        config_file = os.path.expanduser('~/.xonshrc')
        with temp_move_path(config_file, d) as path:
            new_config_path = os.path.join(d, 'new.xonshrc')
            new_config = ''
            if path:
                with open(path, 'r') as f:
                    new_config += f.read()
            new_config += (
                '\n$PROMPT_FIELDS["env_name"] = "({env_name})"\n'
                ''.format(env_name=env_name)
            )
            with open(new_config_path, 'w') as f:
                f.write(new_config)
            yield ['xonsh', '--rc', new_config_path]


@contextmanager
def unknown_shell(shell_name):
    # Assume it's a command and prepare it for Popen.
    yield shell_name.split()


SHELL_COMMANDS = {
    'cmd': cmd_shell,
    'bash': bash_shell,
    'zsh': zsh_shell,
    'xonsh': xonsh_shell,
}
IMMORTAL_SHELLS = {
    'xonsh',
}


def get_shell_command(env_name, shell_name=None, nest=False):
    shell_name = shell_name or os.environ.get('SHELL') or DEFAULT_SHELL
    shell = SHELL_COMMANDS.get(shell_name)
    return shell(env_name, nest) if shell else unknown_shell(shell_name)
