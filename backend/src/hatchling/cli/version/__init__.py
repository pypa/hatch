from __future__ import annotations

import argparse
from typing import Any


def version_impl(
    *,
    called_by_app: bool,  # noqa: ARG001
    force: bool,
    desired_version: str,
) -> None:
    import os

    from hatchling.bridge.app import Application
    from hatchling.metadata.core import ProjectMetadata
    from hatchling.plugin.manager import PluginManager

    app = Application()

    root = os.getcwd()
    plugin_manager = PluginManager()
    metadata = ProjectMetadata(root, plugin_manager)

    if "version" in metadata.config.get("project", {}):
        import tomlkit

        project_file_path = os.path.join(root, "pyproject.toml")

        with open(project_file_path, encoding="utf-8") as fr:
            raw_config = tomlkit.parse(fr.read())
        version = raw_config["project"]["version"]

        if desired_version:
            from hatchling.version.scheme.standard import StandardScheme

            scheme_config = {"validate-bump": False} if force else {}
            scheme = StandardScheme(root, scheme_config)
            updated_version = scheme.update(desired_version, version, {})
            raw_config["project"]["version"] = updated_version

            with open(project_file_path, "w", encoding="utf-8") as fw:
                fw.write(tomlkit.dumps(raw_config))

            app.display_info(f"Old: {version}")
            app.display_info(f"New: {updated_version}")
        else:
            app.display(version)
        return

    source = metadata.hatch.version.source

    version_data = source.get_version_data()
    original_version = version_data["version"]

    if not desired_version:
        app.display(original_version)
        return

    updated_version = metadata.hatch.version.scheme.update(desired_version, original_version, version_data)
    source.set_version(updated_version, version_data)

    app.display_info(f"Old: {original_version}")
    app.display_info(f"New: {updated_version}")


def version_command(subparsers: argparse._SubParsersAction, defaults: Any) -> None:
    parser = subparsers.add_parser("version")
    parser.add_argument("desired_version", default="", nargs="?", **defaults)
    parser.add_argument("--app", dest="called_by_app", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--force", action="store_true", help="Allow an explicit downgrading version to be given")
    parser.set_defaults(func=version_impl)
