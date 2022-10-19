import argparse
from typing import Dict


def metadata_impl(called_by_app: bool, field: None, compact: bool) -> None:
    import json
    import os

    from hatchling.bridge.app import get_application
    from hatchling.metadata.core import ProjectMetadata
    from hatchling.metadata.utils import resolve_metadata_fields
    from hatchling.plugin.manager import PluginManager

    app = get_application(called_by_app)

    root = os.getcwd()
    plugin_manager = PluginManager()
    project_metadata = ProjectMetadata(root, plugin_manager)

    metadata = resolve_metadata_fields(project_metadata)
    if field:  # no cov
        if field not in metadata:
            app.abort(f'Unknown metadata field: {field}')

        md_field = metadata[field]

        if field == 'readme':
            app.display_always(md_field['text'])  # type: ignore
        elif isinstance(md_field, str):
            app.display_always(md_field)
        else:
            app.display_always(json.dumps(md_field, indent=4))
        return

    for key, value in list(metadata.items()):
        if not value:
            metadata.pop(key)

    if compact:
        app.display_always(json.dumps(metadata, separators=(',', ':')))
    else:  # no cov
        app.display_always(json.dumps(metadata, indent=4))


def metadata_command(subparsers: argparse._SubParsersAction, defaults: Dict[str, str]) -> None:
    parser = subparsers.add_parser('metadata')
    parser.add_argument('field', nargs='?')
    parser.add_argument('-c', '--compact', action='store_true')
    parser.add_argument('--app', dest='called_by_app', action='store_true', help=argparse.SUPPRESS)
    parser.set_defaults(func=metadata_impl)
