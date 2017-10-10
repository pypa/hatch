import os

from hatch.utils import ON_WINDOWS
from hatch.venv import locate_exe_dir


def get_conda_new_exe_path(path):  # no cov
    if ON_WINDOWS:
        return os.pathsep.join((
            path, locate_exe_dir(path, check=False), os.path.join(path, 'Library', 'bin')
        ))
    else:
        return locate_exe_dir(path, check=False)
