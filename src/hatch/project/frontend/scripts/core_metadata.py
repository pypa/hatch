from __future__ import annotations

import json
import os

from hatchling.metadata.core import ProjectMetadata
from hatchling.metadata.utils import resolve_metadata_fields
from hatchling.plugin.manager import PluginManager

RUNNER: dict = {}


def main() -> None:
    project_root: str = RUNNER["project_root"]
    output_dir: str = RUNNER["output_dir"]

    project_metadata = ProjectMetadata(project_root, PluginManager())
    core_metadata = resolve_metadata_fields(project_metadata)
    for key, value in list(core_metadata.items()):
        if not value:
            core_metadata.pop(key)

    output = json.dumps(core_metadata)
    with open(os.path.join(output_dir, "output.json"), "w", encoding="utf-8") as f:
        f.write(output)


if __name__ == "__main__":
    main()
