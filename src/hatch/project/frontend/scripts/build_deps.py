from __future__ import annotations

import json
import os

from hatchling.bridge.app import Application
from hatchling.metadata.core import ProjectMetadata
from hatchling.plugin.manager import PluginManager

RUNNER: dict = {}


def main() -> None:
    project_root: str = RUNNER["project_root"]
    output_dir: str = RUNNER["output_dir"]
    targets: list[str] = RUNNER["targets"]

    app = Application()
    plugin_manager = PluginManager()
    metadata = ProjectMetadata(project_root, plugin_manager)

    dependencies: dict[str, None] = {}
    for target_name in targets:
        builder_class = plugin_manager.builder.get(target_name)
        if builder_class is None:
            continue

        builder = builder_class(
            project_root, plugin_manager=plugin_manager, metadata=metadata, app=app.get_safe_application()
        )
        for dependency in builder.config.dependencies:
            dependencies[dependency] = None

    output = json.dumps(list(dependencies))
    with open(os.path.join(output_dir, "output.json"), "w", encoding="utf-8") as f:
        f.write(output)


if __name__ == "__main__":
    main()
