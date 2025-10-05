from __future__ import annotations

import re
import sys
from importlib.metadata import Distribution, DistributionFinder

from packaging.markers import default_environment

from hatch.dep.core import Dependency
from hatch.utils.fs import Path


class InstalledDistributions:
    def __init__(self, *, sys_path: list[str] | None = None, environment: dict[str, str] | None = None) -> None:
        self.__sys_path: list[str] = sys.path if sys_path is None else sys_path
        self.__environment: dict[str, str] = (
            default_environment() if environment is None else environment  # type: ignore[assignment]
        )
        self.__resolver = Distribution.discover(context=DistributionFinder.Context(path=self.__sys_path))
        self.__distributions: dict[str, Distribution] = {}
        self.__search_exhausted = False
        self.__canonical_regex = re.compile(r"[-_.]+")

    def dependencies_in_sync(self, dependencies: list[Dependency]) -> bool:
        return all(self.dependency_in_sync(dependency) for dependency in dependencies)

    def missing_dependencies(self, dependencies: list[Dependency]) -> list[Dependency]:
        return [dependency for dependency in dependencies if not self.dependency_in_sync(dependency)]

    def dependency_in_sync(self, dependency: Dependency, *, environment: dict[str, str] | None = None) -> bool:
        if environment is None:
            environment = self.__environment

        if dependency.marker and not dependency.marker.evaluate(environment):
            return True

        distribution = self[dependency.name]
        if distribution is None:
            return False

        extras = dependency.extras
        if extras:
            transitive_dependencies: list[str] = distribution.metadata.get_all("Requires-Dist", [])
            if not transitive_dependencies:
                return False

            available_extras: list[str] = distribution.metadata.get_all("Provides-Extra", [])

            for dependency_string in transitive_dependencies:
                transitive_dependency = Dependency(dependency_string)
                if not transitive_dependency.marker:
                    continue

                for extra in extras:
                    # FIXME: This may cause a build to never be ready if newer versions do not provide the desired
                    # extra and it's just a user error/typo. See: https://github.com/pypa/pip/issues/7122
                    if extra not in available_extras:
                        return False

                    extra_environment = dict(environment)
                    extra_environment["extra"] = extra
                    if not self.dependency_in_sync(transitive_dependency, environment=extra_environment):
                        return False

        if dependency.specifier and not dependency.specifier.contains(distribution.version):
            return False

        # TODO: handle https://discuss.python.org/t/11938
        if dependency.url:
            direct_url_file = distribution.read_text("direct_url.json")
            if direct_url_file is None:
                return False

            import json

            # https://packaging.python.org/specifications/direct-url/
            direct_url_data = json.loads(direct_url_file)
            url = direct_url_data["url"]
            if "dir_info" in direct_url_data:
                dir_info = direct_url_data["dir_info"]
                editable = dir_info.get("editable", False)
                if editable != dependency.editable:
                    return False

                if Path.from_uri(url) != dependency.path:
                    return False

            if "vcs_info" in direct_url_data:
                vcs_info = direct_url_data["vcs_info"]
                vcs = vcs_info["vcs"]
                commit_id = vcs_info["commit_id"]
                requested_revision = vcs_info.get("requested_revision")

                # Try a few variations, see https://peps.python.org/pep-0440/#direct-references
                if (
                    requested_revision and dependency.url == f"{vcs}+{url}@{requested_revision}#{commit_id}"
                ) or dependency.url == f"{vcs}+{url}@{commit_id}":
                    return True

                if dependency.url in {f"{vcs}+{url}", f"{vcs}+{url}@{requested_revision}"}:
                    import subprocess

                    if vcs == "git":
                        vcs_cmd = [vcs, "ls-remote", url]
                        if requested_revision:
                            vcs_cmd.append(requested_revision)
                    # TODO: add elifs for hg, svn, and bzr https://github.com/pypa/hatch/issues/760
                    else:
                        return False
                    result = subprocess.run(vcs_cmd, capture_output=True, text=True)  # noqa: PLW1510
                    if result.returncode or not result.stdout.strip():
                        return False
                    latest_commit_id, *_ = result.stdout.split()
                    return commit_id == latest_commit_id

                return False

        return True

    def __getitem__(self, item: str) -> Distribution | None:
        item = self.__canonical_regex.sub("-", item).lower()
        possible_distribution = self.__distributions.get(item)
        if possible_distribution is not None:
            return possible_distribution

        if self.__search_exhausted:
            return None

        for distribution in self.__resolver:
            name = distribution.metadata["Name"]
            if name is None:
                continue

            name = self.__canonical_regex.sub("-", name).lower()
            self.__distributions[name] = distribution
            if name == item:
                return distribution

        self.__search_exhausted = True

        return None


def dependencies_in_sync(
    dependencies: list[Dependency], sys_path: list[str] | None = None, environment: dict[str, str] | None = None
) -> bool:  # no cov
    # This function is unused and only temporarily exists for plugin backwards compatibility.
    distributions = InstalledDistributions(sys_path=sys_path, environment=environment)
    return distributions.dependencies_in_sync(dependencies)
