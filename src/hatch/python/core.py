from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hatch.python.distributions import DISTRIBUTIONS, ORDERED_DISTRIBUTIONS
from hatch.python.resolve import get_distribution
from hatch.utils.fs import temp_directory

if TYPE_CHECKING:
    from hatch.python.resolve import Distribution
    from hatch.utils.fs import Path


class InstalledDistribution:
    def __init__(self, path: Path, distribution: Distribution, metadata: dict[str, Any]) -> None:
        self.__path = path
        self.__current_dist = distribution
        self.__metadata = metadata

    @property
    def path(self) -> Path:
        return self.__path

    @property
    def name(self) -> str:
        return self.__current_dist.name

    @property
    def python_path(self) -> Path:
        return self.path / self.__current_dist.python_path

    @property
    def version(self) -> str:
        return self.__current_dist.version.base_version

    @property
    def metadata(self) -> dict[str, Any]:
        return self.__metadata

    def needs_update(self) -> bool:
        new_dist = get_distribution(self.__current_dist.name)
        return new_dist.version > self.__current_dist.version

    @classmethod
    def metadata_filename(cls) -> str:
        return 'hatch-dist.json'


class PythonManager:
    def __init__(self, directory: Path) -> None:
        self.__directory = directory

    @property
    def directory(self) -> Path:
        return self.__directory

    def get_installed(self) -> dict[str, InstalledDistribution]:
        if not self.directory.is_dir():
            return {}

        import json

        installed_distributions: list[InstalledDistribution] = []
        for path in self.directory.iterdir():
            if not (path.name in DISTRIBUTIONS and path.is_dir()):
                continue

            metadata_file = path / InstalledDistribution.metadata_filename()
            if not metadata_file.is_file():
                continue

            metadata = json.loads(metadata_file.read_text())
            distribution = get_distribution(path.name, source=metadata.get('source', ''))
            if not (path / distribution.python_path).is_file():
                continue

            installed_distributions.append(InstalledDistribution(path, distribution, metadata))

        installed_distributions.sort(key=lambda d: ORDERED_DISTRIBUTIONS.index(d.name))
        return {dist.name: dist for dist in installed_distributions}

    def install(self, identifier: str) -> InstalledDistribution:
        import json

        from hatch.utils.network import download_file

        dist = get_distribution(identifier)
        path = self.directory / identifier
        self.directory.ensure_dir_exists()

        with temp_directory() as temp_dir:
            archive_path = temp_dir / dist.archive_name
            unpack_path = temp_dir / identifier
            download_file(archive_path, dist.source, follow_redirects=True)
            dist.unpack(archive_path, unpack_path)

            backup_path = path.with_suffix('.bak')
            if backup_path.is_dir():
                backup_path.wait_for_dir_removed()

            if path.is_dir():
                path.replace(backup_path)

            try:
                unpack_path.replace(path)
            except OSError:
                import shutil

                try:
                    shutil.move(str(unpack_path), str(path))
                except OSError:
                    path.wait_for_dir_removed()
                    if backup_path.is_dir():
                        backup_path.replace(path)

                    raise

        metadata = {'source': dist.source, 'python_path': dist.python_path}
        metadata_file = path / InstalledDistribution.metadata_filename()
        metadata_file.write_text(json.dumps(metadata, indent=2))

        return InstalledDistribution(path, dist, metadata)

    @staticmethod
    def remove(dist: InstalledDistribution) -> None:
        dist.path.wait_for_dir_removed()
