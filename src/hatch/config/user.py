from typing import Optional, cast

import tomli

from ..utils.fs import Path
from .model import RootConfig


class ConfigFile:
    def __init__(self, path: Optional[Path] = None):
        self._path: Optional[Path] = path
        self.model = cast(RootConfig, None)

    @property
    def path(self):
        if self._path is None:
            self._path = self.get_default_location()

        return self._path

    @path.setter
    def path(self, value):
        self._path = value

    def save(self, content=None):
        import tomli_w
        from atomicwrites import atomic_write

        if not content:
            content = tomli_w.dumps(self.model.raw_data).encode('utf-8')

        self.path.ensure_parent_dir_exists()
        with atomic_write(str(self.path), mode='wb', overwrite=True) as f:
            f.write(content)

    def load(self):
        self.model = RootConfig(tomli.loads(self.read()))

    def read(self) -> str:
        return self.path.read_text('utf-8')

    def read_scrubbed(self) -> str:
        import tomli_w

        config = RootConfig(tomli.loads(self.read()))
        config.raw_data.pop('publish', None)
        return tomli_w.dumps(config.raw_data)

    def restore(self):
        import tomli_w

        config = RootConfig({})
        config.parse_fields()

        content = tomli_w.dumps(config.raw_data).encode('utf-8')
        self.save(content)

        self.model = config

    def update(self):  # no cov
        self.model.parse_fields()
        self.save()

    @classmethod
    def get_default_location(cls) -> Path:
        from platformdirs import user_config_dir

        return Path(user_config_dir('hatch', appauthor=False)) / 'config.toml'
