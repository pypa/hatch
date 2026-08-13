from __future__ import annotations

import argparse
from typing import Any


def _display_artifact(app: Any, artifact: str, root: str, directory: str | None) -> None:
    import os

    if os.path.isfile(artifact):
        candidates = [root]
        if directory:
            candidates.append(os.path.dirname(os.path.abspath(directory)))

        for candidate in candidates:
            if candidate and (artifact == candidate or artifact.startswith(candidate + os.sep)):
                app.display_info(os.path.relpath(artifact, candidate))
                return

    app.display_info(artifact)  # no cov


def build_impl(
    *,
    called_by_app: bool,  # noqa: ARG001
    directory: str,
    targets: list[str],
    hooks_only: bool,
    no_hooks: bool,
    clean: bool,
    clean_hooks_after: bool,
    clean_only: bool,
    show_dynamic_deps: bool,
) -> None:
    import os

    from hatchling.bridge.app import Application
    from hatchling.builders.constants import DEFAULT_BUILD_DIRECTORY, BuildEnvVars
    from hatchling.builders.sdist_wheel import build_wheel_from_sdist
    from hatchling.metadata.core import ProjectMetadata
    from hatchling.plugin.manager import PluginManager

    app = Application()

    if hooks_only and no_hooks:
        app.abort("Cannot use both --hooks-only and --no-hooks together")

    root = os.getcwd()
    plugin_manager = PluginManager()
    metadata = ProjectMetadata(root, plugin_manager)

    target_data: dict[str, Any] = {}
    if targets:
        for data in targets:
            target_name, _, version_data = data.partition(":")
            versions = version_data.split(",") if version_data else []
            target_data.setdefault(target_name, []).extend(versions)
    else:  # no cov
        target_data["sdist"] = []
        target_data["wheel"] = []

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
        os.environ[BuildEnvVars.NO_HOOKS] = "true"

    # When both targets are requested, build the wheel from the sdist so the
    # published artifacts match what installers produce from the sdist alone.
    build_wheel_via_sdist = (
        not clean_only
        and not show_dynamic_deps
        and not hooks_only
        and "sdist" in target_data
        and "wheel" in target_data
    )
    if build_wheel_via_sdist:
        ordered_targets = [(name, versions) for name, versions in target_data.items() if name != "wheel"]
        ordered_targets.append(("wheel", target_data["wheel"]))
    else:
        ordered_targets = list(target_data.items())

    # Resolve the output directory against the original project before any
    # temporary sdist extraction changes the effective project root.
    if directory:
        output_directory: str | None = os.path.abspath(directory)
    elif build_wheel_via_sdist:
        output_directory = os.path.join(root, DEFAULT_BUILD_DIRECTORY)
    else:
        output_directory = None

    dynamic_dependencies: dict[str, None] = {}
    sdist_artifact: str | None = None
    for i, (target_name, versions) in enumerate(ordered_targets):
        # Separate targets with a blank line
        if not (clean_only or show_dynamic_deps) and i != 0:  # no cov
            app.display_info()

        builder_class = builders[target_name]

        # Display name before instantiation in case of errors
        if not (clean_only or show_dynamic_deps) and len(target_data) > 1:
            app.display_mini_header(target_name)

        if show_dynamic_deps:
            builder = builder_class(
                root, plugin_manager=plugin_manager, metadata=metadata, app=app.get_safe_application()
            )
            for dependency in builder.config.dynamic_dependencies:
                dynamic_dependencies[dependency] = None

            continue

        if build_wheel_via_sdist and target_name == "wheel":
            if sdist_artifact is None:
                app.abort("Cannot build wheel from sdist because no sdist artifact was produced")

            artifacts = build_wheel_from_sdist(
                sdist_path=sdist_artifact,
                wheel_builder_class=builder_class,
                plugin_manager=plugin_manager,
                app=app.get_safe_application(),
                directory=output_directory,
                versions=versions,
                hooks_only=hooks_only,
                clean=clean,
                clean_hooks_after=clean_hooks_after,
                clean_only=clean_only,
            )
        else:
            builder = builder_class(
                root, plugin_manager=plugin_manager, metadata=metadata, app=app.get_safe_application()
            )
            artifacts = builder.build(
                directory=output_directory if output_directory is not None else directory,
                versions=versions,
                hooks_only=hooks_only,
                clean=clean,
                clean_hooks_after=clean_hooks_after,
                clean_only=clean_only,
            )

        for artifact in artifacts:
            if target_name == "sdist":
                sdist_artifact = artifact

            _display_artifact(app, artifact, root, output_directory if output_directory is not None else directory)

    if show_dynamic_deps:
        app.display(str(list(dynamic_dependencies)))


def build_command(subparsers: argparse._SubParsersAction, defaults: Any) -> None:
    parser = subparsers.add_parser("build")
    parser.add_argument(
        "-d", "--directory", dest="directory", help="The directory in which to build artifacts", **defaults
    )
    parser.add_argument(
        "-t",
        "--target",
        dest="targets",
        action="append",
        help="Comma-separated list of targets to build, overriding project defaults",
        **defaults,
    )
    parser.add_argument("--hooks-only", dest="hooks_only", action="store_true", default=None)
    parser.add_argument("--no-hooks", dest="no_hooks", action="store_true", default=None)
    parser.add_argument("-c", "--clean", dest="clean", action="store_true", default=None)
    parser.add_argument("--clean-hooks-after", dest="clean_hooks_after", action="store_true", default=None)
    parser.add_argument("--clean-only", dest="clean_only", action="store_true")
    parser.add_argument("--show-dynamic-deps", dest="show_dynamic_deps", action="store_true")
    parser.add_argument("--app", dest="called_by_app", action="store_true", help=argparse.SUPPRESS)
    parser.set_defaults(func=build_impl)
