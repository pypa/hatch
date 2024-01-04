from __future__ import annotations

import argparse
from typing import Any


def metadata_impl(
    *,
    called_by_app: bool,  # noqa: ARG001
    field: str,
    compact: bool,
) -> None:
    import json
    import os

    from hatchling.bridge.app import Application
    from hatchling.metadata.core import ProjectMetadata
    from hatchling.metadata.utils import resolve_metadata_fields
    from hatchling.plugin.manager import PluginManager

    app = Application()

    root = os.getcwd()
    plugin_manager = PluginManager()
    project_metadata = ProjectMetadata(root, plugin_manager)

    metadata = resolve_metadata_fields(project_metadata)
    if field:  # no cov
        if field not in metadata:
            app.abort(f'Unknown metadata field: {field}')
        elif field == 'readme':
            app.display(metadata[field]['text'])
        elif isinstance(metadata[field], str):
            app.display(metadata[field])
        else:
            app.display(json.dumps(metadata[field], indent=4))

        return

    for key, value in list(metadata.items()):
        if not value:
            metadata.pop(key)

    if compact:
        app.display(json.dumps(metadata, separators=(',', ':')))
    else:  # no cov
        app.display(json.dumps(metadata, indent=4))


def metadata_command(
    subparsers: argparse._SubParsersAction,
    defaults: Any,  # noqa: ARG001
) -> None:
    parser = subparsers.add_parser('metadata')
    parser.add_argument('field', nargs='?')
    parser.add_argument('-c', '--compact', action='store_true')
    parser.add_argument('--app', dest='called_by_app', action='store_true', help=argparse.SUPPRESS)
    parser.set_defaults(func=metadata_impl)
