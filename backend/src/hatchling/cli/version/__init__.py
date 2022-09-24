import argparse


def version_impl(called_by_app, desired_version):
    import os

    from hatchling.bridge.app import get_application
    from hatchling.metadata.core import ProjectMetadata
    from hatchling.plugin.manager import PluginManager

    app = get_application(called_by_app)

    root = os.getcwd()
    plugin_manager = PluginManager()
    metadata = ProjectMetadata(root, plugin_manager)

    if 'version' in metadata.config.get('project', {}):
        if desired_version:
            app.abort('Cannot set version when it is statically defined by the `project.version` field')
        else:
            app.display_always(app.project.metadata.core.version)
            return

    source = metadata.hatch.version.source

    version_data = source.get_version_data()
    original_version = version_data['version']

    if not desired_version:
        app.display_always(original_version)
        return

    updated_version = metadata.hatch.version.scheme.update(desired_version, original_version, version_data)
    source.set_version(updated_version, version_data)

    app.display_info(f'Old: {original_version}')
    app.display_info(f'New: {updated_version}')


def version_command(subparsers, defaults):
    parser = subparsers.add_parser('version')
    parser.add_argument('desired_version', default='', nargs='?', **defaults)
    parser.add_argument('--app', dest='called_by_app', action='store_true', help=argparse.SUPPRESS)
    parser.set_defaults(func=version_impl)
