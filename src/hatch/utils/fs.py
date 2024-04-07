from __future__ import annotations

import os
import pathlib
import sys
from contextlib import contextmanager, suppress
from functools import cached_property
from typing import TYPE_CHECKING, Any, Generator

from hatch.utils.structures import EnvVars

if TYPE_CHECKING:
    from _typeshed import FileDescriptorLike

# There is special recognition in Mypy for `sys.platform`, not `os.name`
# https://github.com/python/cpython/blob/09d7319bfe0006d9aa3fc14833b69c24ccafdca6/Lib/pathlib.py#L957
if sys.platform == 'win32':
    _PathBase = pathlib.WindowsPath
else:
    _PathBase = pathlib.PosixPath

disk_sync = os.fsync
# https://mjtsai.com/blog/2022/02/17/apple-ssd-benchmarks-and-f_fullsync/
# https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fsync.2.html
if sys.platform == 'darwin':
    import fcntl

    if hasattr(fcntl, 'F_FULLFSYNC'):

        def disk_sync(fd: FileDescriptorLike) -> None:
            fcntl.fcntl(fd, fcntl.F_FULLFSYNC)


class Path(_PathBase):
    @cached_property
    def long_id(self) -> str:
        from base64 import urlsafe_b64encode
        from hashlib import sha256

        path = str(self)
        if sys.platform == 'win32' or sys.platform == 'darwin':
            path = path.casefold()

        digest = sha256(path.encode('utf-8')).digest()
        return urlsafe_b64encode(digest).decode('utf-8')

    @cached_property
    def id(self) -> str:
        return self.long_id[:8]

    def ensure_dir_exists(self) -> None:
        self.mkdir(parents=True, exist_ok=True)

    def ensure_parent_dir_exists(self) -> None:
        self.parent.mkdir(parents=True, exist_ok=True)

    def expand(self) -> Path:
        return Path(os.path.expanduser(os.path.expandvars(self)))

    def remove(self) -> None:
        if self.is_file():
            os.remove(self)
        elif self.is_dir():
            import shutil

            shutil.rmtree(self, ignore_errors=False)

    def wait_for_dir_removed(self, timeout: int = 5) -> None:
        import shutil
        import time

        for _ in range(timeout * 2):
            if self.is_dir():
                shutil.rmtree(self, ignore_errors=True)
                time.sleep(0.5)
            else:
                return

        if self.is_dir():
            shutil.rmtree(self, ignore_errors=False)

    def write_atomic(self, data: str | bytes, *args: Any, **kwargs: Any) -> None:
        from tempfile import mkstemp

        fd, path = mkstemp(dir=self.parent)
        with os.fdopen(fd, *args, **kwargs) as f:
            f.write(data)
            f.flush()
            disk_sync(fd)

        os.replace(path, self)

    @contextmanager
    def as_cwd(self, *args: Any, **kwargs: Any) -> Generator[Path, None, None]:
        origin = os.getcwd()
        os.chdir(self)

        try:
            if args or kwargs:
                with EnvVars(*args, **kwargs):
                    yield self
            else:
                yield self
        finally:
            os.chdir(origin)

    @contextmanager
    def temp_hide(self) -> Generator[Path, None, None]:
        import shutil

        with temp_directory() as temp_dir:
            temp_path = Path(temp_dir, self.name)
            with suppress(FileNotFoundError):
                shutil.move(str(self), temp_dir / self.name)

            try:
                yield temp_path
            finally:
                with suppress(FileNotFoundError):
                    shutil.move(str(temp_path), self)

    if sys.version_info[:2] < (3, 10):

        def resolve(self, strict: bool = False) -> Path:  # noqa: ARG002, FBT001, FBT002
            # https://bugs.python.org/issue38671
            return Path(os.path.realpath(self))


@contextmanager
def temp_directory() -> Generator[Path, None, None]:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as d:
        yield Path(d).resolve()


@contextmanager
def temp_chdir(env_vars: dict[str, str] | None = None) -> Generator[Path, None, None]:
    with temp_directory() as d, d.as_cwd(env_vars=env_vars):
        yield d
