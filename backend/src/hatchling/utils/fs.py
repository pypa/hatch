from __future__ import annotations

import os


def locate_file(root: str, file_name: str, *, boundary: str | None = None) -> str | None:
    """
    Locate a file by searching upward from a root directory until the file is found or a boundary directory is reached.

    Args:
        root (str): The starting directory for the search.
        file_name (str): The name of the file to locate.
        boundary (str | None, optional): The name of a directory that, if reached, stops the search. If None, the search continues up to the filesystem root.

    Returns:
        str | None: The full path to the file if found; otherwise, None.
    """
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
    """
    Convert a local filesystem path to a file URI, handling spaces and platform-specific path separators.

    Args:
        path (str): The local filesystem path to convert.

    Returns:
        str: The file URI corresponding to the given path.
    """
    if os.sep == '/':
        return f'file://{os.path.abspath(path).replace(" ", "%20")}'

    return f'file:///{os.path.abspath(path).replace(" ", "%20").replace(os.sep, "/")}'
