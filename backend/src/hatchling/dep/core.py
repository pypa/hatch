import re
import sys

from packaging.markers import default_environment
from packaging.requirements import Requirement

if sys.version_info >= (3, 8):
    from importlib.metadata import Distribution, DistributionFinder
else:
    from importlib_metadata import Distribution, DistributionFinder


class DistributionCache:
    def __init__(self, sys_path):
        self._resolver = Distribution.discover(context=DistributionFinder.Context(path=sys_path))
        self._distributions = {}
        self._search_exhausted = False
        self._canonical_regex = re.compile(r'[-_.]+')

    def __getitem__(self, item):
        item = self._canonical_regex.sub('-', item).lower()
        possible_distribution = self._distributions.get(item)
        if possible_distribution is not None:
            return possible_distribution
        # Be safe even though the code as-is will never reach this since
        # the first unknown distribution will fail fast
        elif self._search_exhausted:  # no cov
            return

        for distribution in self._resolver:
            name = self._canonical_regex.sub('-', distribution.metadata.get('Name')).lower()
            self._distributions[name] = distribution
            if name == item:
                return distribution

        self._search_exhausted = True


def dependency_in_sync(requirement, environment, installed_distributions):
    if requirement.marker and not requirement.marker.evaluate(environment):
        return True

    distribution = installed_distributions[requirement.name]
    if distribution is None:
        return False

    extras = requirement.extras
    if extras:
        transitive_requirements = distribution.metadata.get_all('Requires-Dist', [])
        if not transitive_requirements:
            return False

        available_extras = distribution.metadata.get_all('Provides-Extra', [])

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
    elif requirement.url:
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

                # Try a few variations, see:
                # https://peps.python.org/pep-0440/#direct-references
                if requirement.url != f'{vcs}+{url}@{commit_id}':
                    if 'requested_revision' in vcs_info:
                        requested_revision = vcs_info['requested_revision']
                        if requirement.url != f'{vcs}+{url}@{requested_revision}#{commit_id}':
                            return False
                    else:
                        return False

    return True


def dependencies_in_sync(requirements, sys_path=None, environment=None):
    if sys_path is None:
        sys_path = sys.path
    if environment is None:
        environment = default_environment()

    installed_distributions = DistributionCache(sys_path)
    return all(dependency_in_sync(requirement, environment, installed_distributions) for requirement in requirements)
