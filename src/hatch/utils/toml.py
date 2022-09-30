import sys
from typing import Any, Dict

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def load_toml_data(data: str) -> Dict[str, Any]:
    return tomllib.loads(data)


def load_toml_file(path: str) -> Dict[str, Any]:
    with open(path, encoding='utf-8') as f:
        return tomllib.loads(f.read())
