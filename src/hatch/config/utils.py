from __future__ import annotations

from typing import TYPE_CHECKING

import tomlkit

if TYPE_CHECKING:
    from tomlkit.items import InlineTable
    from tomlkit.toml_document import TOMLDocument

    from hatch.utils.fs import Path


def save_toml_document(document: TOMLDocument, path: Path):
    path.ensure_parent_dir_exists()
    path.write_atomic(tomlkit.dumps(document), 'w', encoding='utf-8')


def create_toml_document(config: dict) -> InlineTable:
    return tomlkit.item(config)
