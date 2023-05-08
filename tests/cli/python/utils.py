from __future__ import annotations

import json
from typing import TYPE_CHECKING

from hatch.python.core import InstalledDistribution
from hatch.python.resolve import get_distribution

if TYPE_CHECKING:
    from hatch.utils.fs import Path


def write_distribution(directory: Path, name: str):
    dist = get_distribution(name)
    path = directory / dist.name
    path.ensure_dir_exists()
    python_path = path / dist.python_path
    python_path.parent.ensure_dir_exists()
    python_path.touch()
    metadata_file = path / InstalledDistribution.metadata_filename()
    metadata_file.write_text(json.dumps({'source': dist.source, 'python_path': dist.python_path}))


def downgrade_distribution_metadata(dist_dir: Path):
    metadata_file = dist_dir / InstalledDistribution.metadata_filename()
    metadata = json.loads(metadata_file.read_text())
    dist = InstalledDistribution(dist_dir, get_distribution(dist_dir.name), metadata)

    source = metadata['source']
    python_path = metadata['python_path']
    version = dist.version
    new_version = downgrade_version(version)
    new_source = source.replace(version, new_version)
    metadata['source'] = new_source

    # We also modify the Python path because some directory structures are determined
    # by the archive name which is itself determined by the source
    metadata['python_path'] = python_path.replace(version, new_version)
    if python_path != metadata['python_path']:
        new_python_path = dist_dir / metadata['python_path']
        new_python_path.parent.ensure_dir_exists()
        (dist_dir / python_path).rename(new_python_path)

    metadata_file.write_text(json.dumps(metadata))
    return metadata


def downgrade_version(version: str) -> str:
    major_version = version.split('.')[0]
    return version.replace(major_version, str(int(major_version) - 1), 1)
