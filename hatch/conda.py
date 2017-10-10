import os

from hatch.utils import ON_WINDOWS


def get_conda_new_exe_path(path):  # no cov
    if ON_WINDOWS:
        return os.pathsep.join((
            path, os.path.join(path, 'Scripts'), os.path.join(path, 'Library', 'bin')
        ))
    else:
        return os.path.join(path, 'bin')
