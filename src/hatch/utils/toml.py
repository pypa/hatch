from __future__ import annotations

import sys
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def load_toml_data(data: str) -> dict[str, Any]:
    return tomllib.loads(data)


def merge_dictionaries_recursively(primary_dict, secondary_dict):
    merged = primary_dict.copy()

    for key, value in secondary_dict.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_dictionaries_recursively(merged[key], value)
        else:
            merged[key] = value

    return merged


def load_toml_file(path: str) -> dict[str, Any]:
    with open(path, encoding='utf-8') as f:
        return tomllib.loads(f.read())
