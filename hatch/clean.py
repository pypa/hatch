import os
from os.path import join
from pathlib import Path

from hatch.utils import remove_path

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
    '*.pyc',
    '*.pyd',
}
ALL_PATTERNS = DELETE_IN_ROOT | DELETE_EVERYWHERE


def remove_compiled_scripts(d):
    removed = set()

    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith('.pyc'):
                removed.add(join(root, file))

    removed = sorted(removed)

    for p in reversed(removed):
        remove_path(p)

    return removed


def find_globs(d, patterns, matches):
    for root, dirs, files in os.walk(d):
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


def clean_package(d, editable=False):
    removed = set()
    patterns = ALL_PATTERNS.copy()
    if editable:
        patterns.remove('*.egg-info')

    root = Path(d)
    for pattern in patterns:
        for p in root.glob(pattern):
            removed.add(str(p))
            if p.is_dir():
                find_globs(str(p), DELETE_EVERYWHERE, removed)

    find_globs(d, DELETE_EVERYWHERE, removed)

    removed = sorted(removed)

    for p in reversed(removed):
        remove_path(p)

    return removed
