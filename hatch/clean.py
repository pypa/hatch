from collections import deque
from os import remove, walk
from os.path import join
from pathlib import Path
from shutil import rmtree

DELETE_IN_ROOT = {
    '.cache',
    '.coverage',
    '.eggs',
    '.tox',
    'build',
    'dist',
    '*.egg-info',
}
DELETE_EVERYWHERE = {
    '__pycache__',
    '*.pyc'
}
ALL_GLOBS = DELETE_IN_ROOT | DELETE_EVERYWHERE


def get_path(dir_entry):
    return dir_entry.path


def delete_path(path):
    try:
        rmtree(path)
    except OSError:
        try:
            remove(path)
        except FileNotFoundError:
            pass


def clean_package(d):
    removed = []

    root = Path(d)
    for glob in ALL_GLOBS:
        for p in root.glob(glob):
            removed.append(str(p))

    for root, dirs, files in walk(d):
        for d in dirs:
            d = join(root, d)
            for glob in DELETE_EVERYWHERE:
                for p in Path(d).glob(glob):
                    removed.append(str(p))

    for p in removed:
        delete_path(p)

    return sorted(removed)
