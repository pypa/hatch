from __future__ import annotations

import os
from fnmatch import fnmatch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType


class EnvVars(dict):
    def __init__(
        self, env_vars: dict | None = None, include: list[str] | None = None, exclude: list[str] | None = None
    ) -> None:
        super().__init__(os.environ)
        self.old_env = dict(self)

        if include:
            self.clear()
            for env_var, value in self.old_env.items():
                for pattern in include:
                    if fnmatch(env_var, pattern):
                        self[env_var] = value
                        break

        if exclude:
            for env_var in list(self):
                for pattern in exclude:
                    if fnmatch(env_var, pattern):
                        self.pop(env_var)
                        break

        if env_vars:
            self.update(env_vars)

    def __enter__(self) -> None:
        os.environ.clear()
        os.environ.update(self)

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        os.environ.clear()
        os.environ.update(self.old_env)
