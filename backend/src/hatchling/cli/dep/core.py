from __future__ import annotations

import re
import sys
from importlib.metadata import Distribution, DistributionFinder

from packaging.markers import default_environment
from packaging.requirements import Requirement


class DistributionCache:
    def __init__(self, sys_path: list[str]) -> None:
        self._resolver = Distribution.discover(context=DistributionFinder.Context(path=sys_path))
        self._distributions: dict[str, Distribution] = {}
        self._search_exhausted = False
        self._canonical_regex = re.compile(r'[-_.]+')

    def __getitem__(self, item: str) -> Distribution | None:
        item = self._canonical_regex.sub('-', item).lower()
        possible_distribution = self._distributions.get(item)
        if possible_distribution is not None:
            return possible_distribution

        # Be safe even though the code as-is will never reach this since
        # the first unknown distribution will fail fast
        if self._search_exhausted:  # no cov
            return None

        for distribution in self._resolver:
            name = distribution.metadata['Name']
            if name is None:
                continue

            name = self._canonical_regex.sub('-', name).lower()
            self._distributions[name] = distribution
            if name == item:
                return distribution

        self._search_exhausted = True

        return None


def dependency_in_sync(
    requirement: Requirement, environment: dict[str, str], installed_distributions: DistributionCache
) -> bool:
    if requirement.marker and not requirement.marker.evaluate(environment):
        return True

    distribution = installed_distributions[requirement.name]
    if distribution is None:
        return False

    extras = requirement.extras
    if extras:
        transitive_requirements: list[str] = distribution.metadata.get_all('Requires-Dist', [])
        if not transitive_requirements:
            return False

        available_extras: list[str] = distribution.metadata.get_all('Provides-Extra', [])

        for requirement_string in transitive_requirements:
            transitive_requirement = Requirement(requirement_string)
            if not transitive_requirement.marker:
                continue

            for extra in extras:
                # FIXME: This may cause a build to never be ready if newer versions do not provide the desired
                # extra and it's just a user error/typo. See: https://github.com/pypa/pip/issues/7122
                if extra not in available_extras:
                    return False

                extra_environment = dict(environment)
                extra_environment['extra'] = extra
                if not dependency_in_sync(transitive_requirement, extra_environment, installed_distributions):
                    return False

    if requirement.specifier and not requirement.specifier.contains(distribution.version):
        return False

    # TODO: handle https://discuss.python.org/t/11938
    if requirement.url:
        direct_url_file = distribution.read_text('direct_url.json')
        if direct_url_file is not None:
            import json

            # https://packaging.python.org/specifications/direct-url/
            direct_url_data = json.loads(direct_url_file)
            if 'vcs_info' in direct_url_data:
                url = direct_url_data['url']
                vcs_info = direct_url_data['vcs_info']
                vcs = vcs_info['vcs']
                commit_id = vcs_info['commit_id']
                requested_revision = vcs_info.get('requested_revision')

                # Try a few variations, see https://peps.python.org/pep-0440/#direct-references
                if (
                    requested_revision and requirement.url == f'{vcs}+{url}@{requested_revision}#{commit_id}'
                ) or requirement.url == f'{vcs}+{url}@{commit_id}':
                    return True

                if requirement.url in {f'{vcs}+{url}', f'{vcs}+{url}@{requested_revision}'}:
                    import subprocess

                    if vcs == 'git':
                        vcs_cmd = [vcs, 'ls-remote', url]
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


def dependencies_in_sync(
    requirements: list[Requirement], sys_path: list[str] | None = None, environment: dict[str, str] | None = None
) -> bool:
    if sys_path is None:
        sys_path = sys.path
    if environment is None:
        environment = default_environment()  # type: ignore[assignment]

    installed_distributions = DistributionCache(sys_path)
    return all(dependency_in_sync(requirement, environment, installed_distributions) for requirement in requirements)  # type: ignore[arg-type]
