import os
import shutil
from base64 import urlsafe_b64encode


def replace_file(src, dst):
    try:
        os.replace(src, dst)
    # Happens when on different filesystems like /tmp or caused by layering in containers
    except OSError:
        shutil.copy2(src, dst)
        os.remove(src)


def safe_walk(path):
    seen = set()
    for root, dirs, files in os.walk(path, followlinks=True):
        stat = os.stat(root)
        identifier = stat.st_dev, stat.st_ino
        if identifier in seen:
            del dirs[:]
            continue

        seen.add(identifier)
        yield root, dirs, files


def get_known_python_major_versions():
    return map(str, sorted((2, 3)))


def get_relative_path(path, start):
    relative_path = os.path.relpath(path, start)

    # First iteration of `os.walk`
    if relative_path == '.':
        return ''

    return relative_path


def normalize_relative_path(path):
    return os.path.normpath(path).strip(os.sep)


def normalize_relative_directory(path):
    return normalize_relative_path(path) + os.sep


def normalize_inclusion_map(inclusion_map, root):
    normalized_inclusion_map = {}

    for source, relative_path in inclusion_map.items():
        source = os.path.expanduser(os.path.normpath(source))
        if not os.path.isabs(source):
            source = os.path.abspath(os.path.join(root, source))

        normalized_inclusion_map[source] = normalize_relative_path(relative_path)

    return dict(sorted(normalized_inclusion_map.items(), key=lambda item: (item[1].count(os.sep), item[1], item[0])))


def normalize_archive_path(path):
    if os.sep != '/':
        return path.replace(os.sep, '/')

    return path


def format_file_hash(digest):
    # https://peps.python.org/pep-0427/#signed-wheel-files
    return urlsafe_b64encode(digest).decode('ascii').rstrip('=')


def get_reproducible_timestamp():
    """
    Returns an `int` derived from the `SOURCE_DATE_EPOCH` environment variable; see
    https://reproducible-builds.org/specs/source-date-epoch/.

    The default value will always be: `1580601600`
    """
    return int(os.environ.get('SOURCE_DATE_EPOCH', '1580601600'))


def normalize_file_permissions(st_mode):
    """
    https://github.com/takluyver/flit/blob/6a2a8c6462e49f584941c667b70a6f48a7b3f9ab/flit_core/flit_core/common.py#L257

    Normalize the permission bits in the st_mode field from stat to 644/755.

    Popular VCSs only track whether a file is executable or not. The exact
    permissions can vary on systems with different umasks. Normalizing
    to 644 (non executable) or 755 (executable) makes builds more reproducible.
    """
    # Set 644 permissions, leaving higher bits of st_mode unchanged
    new_mode = (st_mode | 0o644) & ~0o133
    if st_mode & 0o100:  # no cov
        new_mode |= 0o111  # Executable: 644 -> 755
    return new_mode


def set_zip_info_mode(zip_info, mode=0o644):
    """
    https://github.com/takluyver/flit/commit/3889583719888aef9f28baaa010e698cb7884904
    """
    zip_info.external_attr = mode << 16
