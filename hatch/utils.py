import glob
import os
import platform
import re
import shutil
from base64 import urlsafe_b64encode
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

__platform = platform.system()
ON_MACOS = os.name == 'mac' or __platform == 'Darwin'
ON_WINDOWS = NEED_SUBPROCESS_SHELL = os.name == 'nt' or __platform == 'Windows'

VENV_FLAGS = {
    '_HATCHING_',
    'VIRTUAL_ENV',
    'CONDA_PREFIX',
}


def venv_active():
    return bool(VENV_FLAGS & set(os.environ)) and not venv_ignored()


def venv_ignored():
    return os.environ.get('_IGNORE_VENV_') == '1'


def get_random_venv_name():
    # Will be length 4, so 16777216 possibilities.
    return urlsafe_b64encode(os.urandom(3)).decode()


def get_admin_command():  # no cov
    if ON_WINDOWS:
        return [
            'runas', r'/user:{}\{}'.format(
                platform.node() or os.environ.get('USERDOMAIN', ''),
                os.environ.get('_DEFAULT_ADMIN_', 'Administrator')
            )
        ]
    # Should we indeed use -H here?
    else:
        admin = os.environ.get('_DEFAULT_ADMIN_', '')
        return ['sudo', '-H'] + (['--user={}'.format(admin)] if admin else [])


def find_project_root(d=None, max_depth=3):
    path = Path(d or os.getcwd())
    root = path.drive + path.root
    path = str(path)

    while max_depth >= 0:
        project_file = os.path.join(path, 'pyproject.toml')
        setup_file = os.path.join(path, 'setup.py')

        if os.path.isfile(project_file) or os.path.isfile(setup_file):
            return path
        elif path == root:
            max_depth = -1
            continue

        max_depth -= 1
        path = os.path.dirname(path)
    else:
        raise Exception(
            'Unable to find project home. Are you sure '
            "you're inside a project directory?"
        )


def is_project(d=None):
    return os.path.isfile(os.path.join(d or os.getcwd(), 'setup.py'))


def is_os_64bit():  # no cov
    # https://stackoverflow.com/a/12578715/5854007
    return platform.machine().endswith('64')


def conda_available():  # no cov
    return not not shutil.which('conda')


def get_requirements_file(d, dev=False):
    d = d or os.getcwd()

    reqs = os.path.join(d, 'requirements.txt')
    if dev or not os.path.exists(reqs):
        paths = set(glob.iglob(os.path.join(d, '*requirements*.txt')))
        paths.discard(reqs)
        if not paths:
            return
        reqs = sorted(paths)[0]

    return reqs


def ensure_dir_exists(d):
    if not os.path.exists(d):
        os.makedirs(d)


def create_file(fname):
    ensure_dir_exists(os.path.dirname(os.path.abspath(fname)))
    with open(fname, 'a'):
        os.utime(fname, times=None)


def download_file(url, fname):
    req = urlopen(url)
    with open(fname, 'wb') as f:
        while True:
            chunk = req.read(16384)
            if not chunk:
                break
            f.write(chunk)
            f.flush()


def copy_path(path, d):
    if os.path.isdir(path):
        shutil.copytree(
            path,
            os.path.join(d, basepath(path)),
            copy_function=shutil.copy
        )
    else:
        shutil.copy(path, d)


def remove_path(path):
    try:
        shutil.rmtree(path)
    except (FileNotFoundError, OSError):
        try:
            os.remove(path)
        except (FileNotFoundError, PermissionError):
            pass


def resolve_path(path):
    try:
        path = str(Path(path).resolve())
    # FUTURE: Remove this when we drop 3.5.
    except FileNotFoundError:  # no cov
        return ''
    return path if os.path.exists(path) else ''


def basepath(path):
    return os.path.basename(os.path.normpath(path))


def get_current_year():
    return str(datetime.now().year)


def normalize_package_name(package_name):
    return re.sub(r"[-_.]+", "_", package_name).lower()


@contextmanager
def chdir(d, cwd=None):
    origin = cwd or os.getcwd()
    os.chdir(d)

    try:
        yield
    finally:
        os.chdir(origin)


@contextmanager
def temp_chdir(cwd=None):
    with TemporaryDirectory() as d:
        origin = cwd or os.getcwd()
        os.chdir(d)

        try:
            yield resolve_path(d)
        finally:
            os.chdir(origin)


@contextmanager
def env_vars(evars, ignore=None):
    ignore = ignore or {}
    ignored_evars = {}
    old_evars = {}

    for ev in evars:
        if ev in os.environ:
            old_evars[ev] = os.environ[ev]
        os.environ[ev] = evars[ev]

    for ev in ignore:
        if ev in os.environ:  # no cov
            ignored_evars[ev] = os.environ[ev]
            os.environ.pop(ev)

    try:
        yield
    finally:
        for ev in evars:
            if ev in old_evars:
                os.environ[ev] = old_evars[ev]
            else:
                os.environ.pop(ev)

        for ev in ignored_evars:
            os.environ[ev] = ignored_evars[ev]


@contextmanager
def temp_move_path(path, d):
    if os.path.exists(path):
        dst = shutil.move(path, d)

        try:
            yield dst
        finally:
            try:
                os.replace(dst, path)
            except OSError:  # no cov
                shutil.move(dst, path)
    else:
        try:
            yield
        finally:
            remove_path(path)


def is_setup_managed(setup_file):
    try:
        with open(setup_file) as f:
            contents = f.readlines()
    except FileNotFoundError:
        return False

    setup_header = re.compile(r'#+\sMaintained by Hatch\s#+')
    if setup_header.match(contents[0]):
        return True

    return False


def parse_setup(setup_file):
    with open(setup_file) as f:
        contents = f.readlines()

    user_def_start = re.compile(r'#+\sBEGIN USER OVERRIDES\s#+')
    user_def_end = re.compile(r'#+\sEND USER OVERRIDES\s#+')
    user_defined_snippet = []
    in_user_defined_section = False
    user_defined_snippet_is_valid = False
    place_holder_text = ['# Add your customizations in this section.']

    for line in contents:
        if user_def_start.match(line):
            in_user_defined_section = True
            continue
        if in_user_defined_section:
            if line.strip() in place_holder_text:
                continue
            if user_def_end.match(line):
                user_defined_snippet_is_valid = True
                break
            user_defined_snippet.append(line)

    if user_defined_snippet_is_valid:
        return ''.join(user_defined_snippet)
    else:
        raise Exception('User-defined section did not end correctly.')
