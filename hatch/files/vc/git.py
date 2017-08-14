import os
import subprocess

from hatch.files.ignore import GitIgnore
from hatch.structures import File
from hatch.utils import NEED_SUBPROCESS_SHELL


class GitAttributes(File):
    def __init__(self):
        super(GitAttributes, self).__init__(
            '.gitattributes',
            (
                '# Auto detect text files and perform LF normalization\n'
                '* text=auto\n'
            )
        )


def setup_git(d, package_name):
    if not os.path.exists(os.path.join(d, '.git')):  # no cov
        try:
            subprocess.run(['git', 'init', '--quiet'], shell=NEED_SUBPROCESS_SHELL)
        except:
            print('Could not find `git` executable')
        GitAttributes().write(d)
        GitIgnore(package_name).write(d)
