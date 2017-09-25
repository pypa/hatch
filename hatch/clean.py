import itertools
import os
from os.path import join
from pathlib import Path

from hatch.utils import is_project, remove_path

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
    '*.pyo',
}
ALL_PATTERNS = DELETE_IN_ROOT | DELETE_EVERYWHERE


def remove_compiled_scripts(d, detect_project=True):
    removed = set()

    for root, _, files in generate_walker(d, detect_project):
        for file in files:
            if file.endswith('.pyc'):
                removed.add(join(root, file))

    removed = sorted(removed)

    for p in reversed(removed):
        remove_path(p)

    return removed


def find_globs(walker, patterns, matches):
    for root, dirs, files in walker:
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


def clean_package(d, editable=False, detect_project=True):
    removed = set()
    patterns = ALL_PATTERNS.copy()
    if editable:
        patterns.remove('*.egg-info')

    root = Path(d)
    for pattern in patterns:
        for p in root.glob(pattern):
            full_path = str(p)
            removed.add(full_path)
            if p.is_dir():
                find_globs(os.walk(full_path), DELETE_EVERYWHERE, removed)

    find_globs(generate_walker(d, detect_project), DELETE_EVERYWHERE, removed)

    removed = sorted(removed)

    for p in reversed(removed):
        remove_path(p)

    return removed


def generate_walker(d, detect_project=True):
    walker = os.walk(d)
    r, dirs, f = next(walker)

    try:
        if detect_project and is_project(d):
            dirs.remove('venv')
    except ValueError:
        pass

    return itertools.chain(((r, dirs, f),), walker)
