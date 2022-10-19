from __future__ import annotations

import os
from collections.abc import Iterable
from fnmatch import fnmatch


class EnvVars(dict):
    def __init__(
        self,
        env_vars: dict[str, str] | None = None,
        include: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
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

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        os.environ.clear()
        os.environ.update(self.old_env)
