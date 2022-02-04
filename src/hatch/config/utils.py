import tomlkit
from atomicwrites import atomic_write
from tomlkit.toml_document import TOMLDocument

from ..utils.fs import Path


def save_toml_document(document: TOMLDocument, path: Path):
    path.ensure_parent_dir_exists()
    with atomic_write(str(path), mode='wb', overwrite=True) as f:
        f.write(tomlkit.dumps(document).encode('utf-8'))


def create_toml_document(config: dict) -> TOMLDocument:
    return tomlkit.item(config)
