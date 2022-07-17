import argparse


def build_impl(called_by_app, directory, targets, hooks_only, no_hooks, clean, clean_hooks_after, clean_only):
    import os

    from hatchling.bridge.app import get_application
    from hatchling.builders.constants import BuildEnvVars
    from hatchling.metadata.core import ProjectMetadata
    from hatchling.plugin.manager import PluginManager

    app = get_application(called_by_app)

    if hooks_only and no_hooks:
        app.abort('Cannot use both --hooks-only and --no-hooks together')

    root = os.getcwd()
    plugin_manager = PluginManager()
    metadata = ProjectMetadata(root, plugin_manager)

    target_data = {}
    if targets:
        for data in targets:
            target_name, _, version_data = data.partition(':')
            versions = version_data.split(',') if version_data else []
            target_data.setdefault(target_name, []).extend(versions)
    else:  # no cov
        target_data['sdist'] = []
        target_data['wheel'] = []

    builders = {}
    unknown_targets = []
    for target_name in target_data:
        builder_class = plugin_manager.builder.get(target_name)
        if builder_class is None:
            unknown_targets.append(target_name)
        else:
            builders[target_name] = builder_class

    if unknown_targets:
        app.abort(f"Unknown build targets: {', '.join(sorted(unknown_targets))}")

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
