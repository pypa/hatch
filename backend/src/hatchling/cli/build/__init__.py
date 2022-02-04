import argparse


def build_impl(called_by_app, directory, targets, hooks_only, no_hooks, clean, clean_hooks_after, clean_only):
    import os
    from collections import OrderedDict

    from ...builders.constants import BuildEnvVars
    from ...metadata.core import ProjectMetadata
    from ...plugin.manager import PluginManager

    if called_by_app:
        from ...bridge.app import InvokedApplication

        app = InvokedApplication()
    else:  # no cov
        from ...bridge.app import Application

        app = Application()

    if hooks_only and no_hooks:
        app.abort('Cannot use both --hooks-only and --no-hooks together')

    root = os.getcwd()
    plugin_manager = PluginManager()
    metadata = ProjectMetadata(root, plugin_manager)

    target_data = OrderedDict()
    if targets:
        for data in targets:
            target_name, _, version_data = data.partition(':')
            versions = version_data.split(',') if version_data else []
            target_data.setdefault(target_name, []).extend(versions)
    else:  # no cov
        for target_name in metadata.hatch.build_targets:
            target_data[target_name] = []

    if not target_data:  # no cov
        app.display_error('No targets defined in project configuration.')
        app.display_error('Add one or more of the following build targets to pyproject.toml:\n')

        builders = plugin_manager.builder.collect()
        for target_name in sorted(builders):
            app.display_error('[tool.hatch.build.targets.{}]'.format(target_name))

        app.abort()

    builders = OrderedDict()
    unknown_targets = []
    for target_name in target_data:
        builder_class = plugin_manager.builder.get(target_name)
        if builder_class is None:
            unknown_targets.append(target_name)
        else:
            builders[target_name] = builder_class

    if unknown_targets:
        app.abort('Unknown build targets: {}'.format(', '.join(sorted(unknown_targets))))

    # We guarantee that builds occur within the project directory
    root = os.getcwd()

    if no_hooks:
        os.environ[BuildEnvVars.NO_HOOKS] = 'true'

    for i, (target_name, versions) in enumerate(target_data.items()):
        # Separate targets with a blank line
        if not clean_only and i != 0:  # no cov
            app.display_info()

        builder_class = builders[target_name]

        # Display name before instantiation in case of errors
        if not clean_only:
            app.display_mini_header(target_name)

        builder = builder_class(root, plugin_manager=plugin_manager, metadata=metadata, app=app.get_safe_application())

        for artifact in builder.build(
            directory=directory,
            versions=versions,
            hooks_only=hooks_only,
            clean=clean,
            clean_hooks_after=clean_hooks_after,
            clean_only=clean_only,
        ):
            if os.path.isfile(artifact) and artifact.startswith(root):
                app.display_info(os.path.relpath(artifact, root))
            else:  # no cov
                app.display_info(artifact)


def build_command(subparsers, defaults):
    parser = subparsers.add_parser('build')
    parser.add_argument(
        '-d',
        '--directory',
        dest='directory',
        help='The directory in which to build artifacts',
        **defaults
    )
    parser.add_argument(
        '-t',
        '--target',
        dest='targets',
        action='append',
        help='Comma-separated list of targets to build, overriding project defaults',
        **defaults
    )
    parser.add_argument('--hooks-only', dest='hooks_only', action='store_true', default=None)
    parser.add_argument('--no-hooks', dest='no_hooks', action='store_true', default=None)
    parser.add_argument('-c', '--clean', dest='clean', action='store_true', default=None)
    parser.add_argument('--clean-hooks-after', dest='clean_hooks_after', action='store_true', default=None)
    parser.add_argument('--clean-only', dest='clean_only', action='store_true')
    parser.add_argument('--app', dest='called_by_app', action='store_true', help=argparse.SUPPRESS)
    parser.set_defaults(func=build_impl)
