from hatch.utils import NEED_SUBPROCESS_SHELL

DEFAULT_SHELL = 'cmd' if NEED_SUBPROCESS_SHELL else 'bash'

SHELL_COMMANDS = {
    'cmd': ['cmd', '/k'],
    'bash': ['bash'],  # '--init-file', '<(echo -e "source ~/.bashrc\nPS1=\"(ok) $PS1\"")'],
    'zsh': ['zsh'],
}
