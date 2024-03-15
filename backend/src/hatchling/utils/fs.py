from __future__ import annotations

import os


def locate_file(root: str, file_name: str, *, boundary: str | None = None) -> str | None:
    while True:
        file_path = os.path.join(root, file_name)
        if os.path.isfile(file_path):
            return file_path

        if boundary is not None and os.path.exists(os.path.join(root, boundary)):
            return None

        new_root = os.path.dirname(root)
        if new_root == root:
            return None

        root = new_root


def path_to_uri(path: str) -> str:
    if os.sep == '/':
        return f'file://{os.path.abspath(path).replace(" ", "%20")}'

    return f'file:///{os.path.abspath(path).replace(" ", "%20").replace(os.sep, "/")}'
