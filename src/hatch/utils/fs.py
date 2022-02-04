from __future__ import annotations

import os
import pathlib
import sys
from contextlib import contextmanager
from typing import Generator

from .structures import EnvVars

# There is special recognition in Mypy for `sys.platform`, not `os.name`
# https://github.com/python/cpython/blob/09d7319bfe0006d9aa3fc14833b69c24ccafdca6/Lib/pathlib.py#L957
if sys.platform == 'win32':
    _PathBase = pathlib.WindowsPath
else:
    _PathBase = pathlib.PosixPath


class Path(_PathBase):
    def ensure_dir_exists(self):
        self.mkdir(parents=True, exist_ok=True)

    def ensure_parent_dir_exists(self):
        self.parent.mkdir(parents=True, exist_ok=True)

    def resolve(self, strict=False) -> Path:
        # https://bugs.python.org/issue38671
        return Path(os.path.realpath(self))

    def remove(self):
        if self.is_file():
            os.remove(self)
        elif self.is_dir():
            import shutil

            shutil.rmtree(self, ignore_errors=False)

    @contextmanager
    def as_cwd(self, *args, **kwargs) -> Generator[Path, None, None]:
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
        with temp_directory() as temp_dir:
            temp_path = Path(temp_dir, self.name)
            try:
                self.replace(temp_dir / self.name)
            except FileNotFoundError:
                pass

            try:
                yield temp_path
            finally:
                try:
                    temp_path.replace(self)
                except FileNotFoundError:
                    pass


@contextmanager
def temp_directory() -> Generator[Path, None, None]:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as d:
        yield Path(d).resolve()


@contextmanager
def temp_chdir(env_vars=None) -> Generator[Path, None, None]:
    with temp_directory() as d:
        with d.as_cwd(env_vars=env_vars):
            yield d
