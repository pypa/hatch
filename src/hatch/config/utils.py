import tomlkit
from tomlkit.toml_document import TOMLDocument

from hatch.utils.fs import Path


def save_toml_document(document: TOMLDocument, path: Path):
    path.ensure_parent_dir_exists()
    path.write_atomic(tomlkit.dumps(document), 'w')


def create_toml_document(config: dict) -> TOMLDocument:
    return tomlkit.item(config)
