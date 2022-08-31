from __future__ import annotations

import re

from hatch.config.model import RootConfig
from hatch.utils.fs import Path


class Project:
    def __init__(self, path: Path, *, name: str = None, config=None):
        self._path = path

        # From app config
        self.chosen_name = name

        # Location of pyproject.toml
        self._project_file_path: Path | None = None

        self._root_searched = False
        self._root: Path | None = None
        self._raw_config = config
        self._plugin_manager = None
        self._metadata = None
        self._config = None

    @property
    def plugin_manager(self):
        if self._plugin_manager is None:
            from hatch.plugin.manager import PluginManager

            self._plugin_manager = PluginManager()

        return self._plugin_manager

    @property
    def config(self):
        if self._config is None:
            from hatch.project.config import ProjectConfig

            self._config = ProjectConfig(self.location, self.metadata.hatch.config, self.plugin_manager)

        return self._config

    @property
    def root(self) -> Path | None:
        if not self._root_searched:
            self._root = self.find_project_root()
            self._root_searched = True

        return self._root

    @property
    def location(self) -> Path:
        return self.root or self._path

    @classmethod
    def from_config(cls, config: RootConfig, project: str) -> Project | None:
        # Disallow empty strings
        if not project:
            return None

        if project in config.projects:
            location = config.projects[project].location
            if location:
                return cls(Path(location).resolve(), name=project)
        else:
            for project_dir in config.dirs.project:
                if not project_dir:
                    continue

                location = Path(project_dir, project)
                if location.is_dir():
                    return cls(Path(location).resolve(), name=project)

    def find_project_root(self) -> Path | None:
        path = self._path

        while True:
            possible_file = path.joinpath('pyproject.toml')
            if possible_file.is_file():
                self._project_file_path = possible_file
                return path
            elif path.joinpath('setup.py').is_file():
                return path

            new_path = path.parent
            if new_path == path:
                return None

            path = new_path

    @staticmethod
    def canonicalize_name(name: str, strict=True) -> str:
        if strict:
            return re.sub(r'[-_.]+', '-', name).lower()
        else:
            # Used for creating new projects
            return re.sub(r'[-_. ]+', '-', name).lower()

    @property
    def metadata(self):
        if self._metadata is None:
            from hatchling.metadata.core import ProjectMetadata

            self._metadata = ProjectMetadata(self.location, self.plugin_manager, self.raw_config)

        return self._metadata

    @property
    def raw_config(self):
        if self._raw_config is None:
            if self.root is None or self._project_file_path is None:
                # Assume no pyproject.toml e.g. environment management only
                self._raw_config = {'project': {'name': self.location.name}}
            else:
                from hatch.utils.toml import load_toml_file

                self._raw_config = load_toml_file(str(self._project_file_path))

        return self._raw_config

    def save_config(self, config):
        import tomlkit

        with open(str(self._project_file_path), 'w', encoding='utf-8') as f:
            f.write(tomlkit.dumps(config))

    @staticmethod
    def initialize(project_file_path, template_config):
        import tomlkit

        with open(str(project_file_path), encoding='utf-8') as f:
            raw_config = tomlkit.parse(f.read())

        build_system_config = raw_config.setdefault('build-system', {})

        build_system_config.clear()
        build_system_config['requires'] = ['hatchling']
        build_system_config['build-backend'] = 'hatchling.build'

        project_config = raw_config.get('project')
        if project_config is None:
            raw_config['project'] = project_config = {}

        project_name = project_config.get('name')
        if not project_name:
            project_config['name'] = template_config['project_name_normalized']

        project_description = project_config.get('description')
        if not project_description:
            project_config['description'] = template_config['description']

        project_config['dynamic'] = ['version']

        tool_config = raw_config.get('tool')
        if tool_config is None:
            raw_config['tool'] = tool_config = {}

        hatch_config = tool_config.get('hatch')
        if hatch_config is None:
            tool_config['hatch'] = hatch_config = {}

        version_config = hatch_config.get('version')
        if version_config is None:
            hatch_config['version'] = version_config = {}

        version_config.clear()
        version_config['path'] = f'{template_config["package_name"]}/__init__.py'

        with open(str(project_file_path), 'w', encoding='utf-8') as f:
            f.write(tomlkit.dumps(raw_config))
