from __future__ import annotations

from typing import cast

from hatch.config.model import RootConfig
from hatch.utils.fs import Path
from hatch.utils.toml import load_toml_data


class ConfigFile:
    def __init__(self, path: Path | None = None):
        self._path: Path | None = path
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

        if not content:
            content = tomli_w.dumps(self.model.raw_data)

        self.path.ensure_parent_dir_exists()
        self.path.write_atomic(content, 'w', encoding='utf-8')

    def load(self):
        self.model = RootConfig(load_toml_data(self.read()))

    def read(self) -> str:
        return self.path.read_text('utf-8')

    def read_scrubbed(self) -> str:
        import tomli_w

        config = RootConfig(load_toml_data(self.read()))
        config.raw_data.pop('publish', None)
        return tomli_w.dumps(config.raw_data)

    def restore(self):
        import tomli_w

        config = RootConfig({})
        config.parse_fields()

        content = tomli_w.dumps(config.raw_data)
        self.save(content)

        self.model = config

    def update(self):  # no cov
        self.model.parse_fields()
        self.save()

    @classmethod
    def get_default_location(cls) -> Path:
        from platformdirs import user_config_dir

        return Path(user_config_dir('hatch', appauthor=False)) / 'config.toml'
