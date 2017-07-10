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
ALL_PATTERNS = DELETE_IN_ROOT | DELETE_EVERYWHERE


def delete_path(path):
    try:
        rmtree(path)
    except OSError:
        try:
            remove(path)

        # Since we delete files first by reverse iterating
        # over sorted path names, this should never occur.
        except FileNotFoundError:  # no cov
            pass


def find_globs(d, patterns, matches):
    for root, dirs, files in walk(d):
        for d in dirs:
            d = join(root, d)
            for pattern in patterns:
                for p in Path(d).glob(pattern):
                    matches.add(str(p))

        sub_files = set()
        for p in matches:
            if root.startswith(p):
                for f in files:
                    sub_files.add(join(root, f))

        matches.update(sub_files)


def clean_package(d):
    removed = set()

    root = Path(d)
    for pattern in ALL_PATTERNS:
        for p in root.glob(pattern):
            removed.add(str(p))
            if p.is_dir():
                find_globs(str(p), DELETE_EVERYWHERE, removed)

    find_globs(d, DELETE_EVERYWHERE, removed)

    removed = sorted(removed)

    for p in reversed(removed):
        delete_path(p)

    return removed
