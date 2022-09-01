import argparse


def metadata_impl(called_by_app, field, compact):
    import json
    import os

    from hatchling.bridge.app import get_application
    from hatchling.metadata.core import ProjectMetadata
    from hatchling.plugin.manager import PluginManager

    app = get_application(called_by_app)

    root = os.getcwd()
    plugin_manager = PluginManager()
    project_metadata = ProjectMetadata(root, plugin_manager)
    core_metadata = project_metadata.core

    # https://peps.python.org/pep-0621/
    metadata = {
        'name': core_metadata.name,
        'version': project_metadata.version,
        'description': core_metadata.description,
        'readme': core_metadata.readme,
        'requires-python': core_metadata.requires_python,
        'license': core_metadata.license_expression or core_metadata.license,
        'authors': core_metadata.authors,
        'maintainers': core_metadata.maintainers,
        'keywords': core_metadata.keywords,
        'classifiers': core_metadata.classifiers,
        'urls': core_metadata.urls,
        'scripts': core_metadata.scripts,
        'gui-scripts': core_metadata.gui_scripts,
        'entry-points': core_metadata.entry_points,
        'dependencies': core_metadata.dependencies,
        'optional-dependencies': core_metadata.optional_dependencies,
    }
    if field:
        if field not in metadata:
            app.abort(f'Unknown metadata field: {field}')

        app.display_info(metadata[field])
        return

    for key, value in list(metadata.items()):
        if not value:
            metadata.pop(key)

    if compact:
        app.display_info(json.dumps(metadata, separators=(',', ':')))
    else:
        app.display_info(json.dumps(metadata, indent=4))


def metadata_command(subparsers, defaults):
    parser = subparsers.add_parser('metadata')
    parser.add_argument('field', nargs='?')
    parser.add_argument('-c', '--compact', action='store_true')
    parser.add_argument('--app', dest='called_by_app', action='store_true', help=argparse.SUPPRESS)
    parser.set_defaults(func=metadata_impl)
