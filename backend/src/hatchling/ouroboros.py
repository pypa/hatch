from __future__ import annotations

import os
import re
from ast import literal_eval
from typing import Any

from hatchling.build import *  # noqa: F403


def read_dependencies() -> list[str]:
    pattern = r'^dependencies = (\[.*?\])$'

    with open(os.path.join(os.getcwd(), 'pyproject.toml'), encoding='utf-8') as f:
        # Windows \r\n prevents match
        contents = '\n'.join(line.rstrip() for line in f)

    match = re.search(pattern, contents, flags=re.MULTILINE | re.DOTALL)
    if match is None:
        message = 'No dependencies found'
        raise ValueError(message)

    return literal_eval(match.group(1))


def get_requires_for_build_sdist(  # type: ignore[no-redef]
    config_settings: dict[str, Any] | None = None,  # noqa: ARG001
) -> list[str]:
    """
    https://peps.python.org/pep-0517/#get-requires-for-build-sdist
    """
    return read_dependencies()


def get_requires_for_build_wheel(  # type: ignore[no-redef]
    config_settings: dict[str, Any] | None = None,  # noqa: ARG001
) -> list[str]:
    """
    https://peps.python.org/pep-0517/#get-requires-for-build-wheel
    """
    return read_dependencies()


def get_requires_for_build_editable(  # type: ignore[no-redef]
    config_settings: dict[str, Any] | None = None,  # noqa: ARG001
) -> list[str]:
    """
    https://peps.python.org/pep-0660/#get-requires-for-build-editable
    """
    from hatchling.builders.constants import EDITABLES_REQUIREMENT

    return [*read_dependencies(), EDITABLES_REQUIREMENT]
