from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from configparser import ConfigParser

    from hatch.utils.fs import Path


class PatchedCoverageConfig:
    def __init__(self, project_root: Path, data_dir: Path) -> None:
        self.project_root = project_root
        self.data_dir = data_dir

    @cached_property
    def user_config_path(self) -> Path:
        # https://coverage.readthedocs.io/en/7.4.4/config.html#sample-file
        return (
            dedicated_coverage_file
            if (dedicated_coverage_file := self.project_root.joinpath('.coveragerc')).is_file()
            else self.project_root.joinpath('pyproject.toml')
        )

    @cached_property
    def internal_config_path(self) -> Path:
        return self.data_dir / 'coverage' / self.project_root.id / self.user_config_path.name

    def write_config_file(self) -> None:
        self.internal_config_path.parent.ensure_dir_exists()
        if self.internal_config_path.name == '.coveragerc':
            from configparser import ConfigParser

            cfg = ConfigParser()
            cfg.read(str(self.user_config_path))

            if 'run' not in cfg:
                cfg['run'] = {'parallel': 'true'}
                self._write_ini(cfg)
                return

            cfg['run']['parallel'] = 'true'
            self._write_ini(cfg)
        else:
            import tomli_w

            from hatch.utils.toml import load_toml_data

            project_data = load_toml_data(self.user_config_path.read_text())
            project_data.setdefault('tool', {}).setdefault('coverage', {}).setdefault('run', {})['parallel'] = True
            self.internal_config_path.write_text(tomli_w.dumps(project_data))

    def _write_ini(self, cfg: ConfigParser) -> None:
        with self.internal_config_path.open('w', encoding='utf-8') as f:
            cfg.write(f)
