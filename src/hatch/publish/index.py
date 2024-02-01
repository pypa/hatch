from __future__ import annotations

import re
from typing import Iterable

from hatch.publish.plugin.interface import PublisherInterface
from hatch.utils.fs import Path
from hatchling.metadata.utils import normalize_project_name


class IndexPublisher(PublisherInterface):
    PLUGIN_NAME = 'index'

    def get_repos(self):
        global_plugin_config = self.plugin_config.copy()
        defined_repos = self.plugin_config.pop('repos', {})
        self.plugin_config.pop('repo', None)

        # Normalize type
        repos = {}
        for repo, data in defined_repos.items():
            if isinstance(data, str):
                repos[repo] = {'url': data}
            elif not isinstance(data, dict):
                self.app.abort(f'Hatch config field `publish.index.repos.{repo}` must be a string or a mapping')
            elif 'url' not in data:
                self.app.abort(f'Hatch config field `publish.index.repos.{repo}` must define a `url` key')
            else:
                repos[repo] = data

        # Ensure PyPI correct
        for repo, url in (
            ('main', 'https://upload.pypi.org/legacy/'),
            ('test', 'https://test.pypi.org/legacy/'),
        ):
            repos.setdefault(repo, {})['url'] = url

        # Populate defaults
        for config in repos.values():
            for key, value in global_plugin_config.items():
                config.setdefault(key, value)

        return repos

    def publish(self, artifacts: list, options: dict):
        """
        https://warehouse.readthedocs.io/api-reference/legacy.html#upload-api
        """
        from collections import defaultdict

        from hatch.index.core import PackageIndex
        from hatch.index.publish import get_sdist_form_data, get_wheel_form_data
        from hatch.publish.auth import AuthenticationCredentials

        if not artifacts:
            from hatchling.builders.constants import DEFAULT_BUILD_DIRECTORY

            artifacts = [DEFAULT_BUILD_DIRECTORY]

        repo = options['repo'] if 'repo' in options else self.plugin_config.get('repo', 'main')
        repos = self.get_repos()
        repo_config: dict[str, str] = repos[repo] if repo in repos else {'url': repo}
        credentials = AuthenticationCredentials(
            app=self.app,
            cache_dir=self.cache_dir,
            options=options,
            repo=repo,
            repo_config=repo_config,
        )

        index = PackageIndex(
            repo_config['url'],
            user=credentials.username,
            auth=credentials.password,
            ca_cert=options.get('ca_cert', repo_config.get('ca-cert')),
            client_cert=options.get('client_cert', repo_config.get('client-cert')),
            client_key=options.get('client_key', repo_config.get('client-key')),
        )

        existing_artifacts: dict[str, set[str]] = {}

        # Use as an ordered set
        project_versions: dict[str, dict[str, None]] = defaultdict(dict)

        artifacts_found = False
        for artifact in recurse_artifacts(artifacts, self.root):
            if artifact.name.endswith('.whl'):
                data = get_wheel_form_data(artifact)
            elif artifact.name.endswith('.tar.gz'):
                data = get_sdist_form_data(artifact)
            else:
                continue

            artifacts_found = True

            for field in ('name', 'version'):
                if field not in data:
                    self.app.abort(f'Missing required field `{field}` in artifact: {artifact}')

            try:
                displayed_path = str(artifact.relative_to(self.root))
            except ValueError:
                displayed_path = str(artifact)

            self.app.display_info(f'{displayed_path} ...', end=' ')

            project_name = normalize_project_name(data['name'])
            if project_name not in existing_artifacts:
                try:
                    response = index.get_simple_api(project_name)
                    response.raise_for_status()
                except Exception:  # no cov  # noqa: BLE001
                    existing_artifacts[project_name] = set()
                else:
                    existing_artifacts[project_name] = set(parse_artifacts(response.text))

            if artifact.name in existing_artifacts[project_name]:
                self.app.display_warning('already exists')
                continue

            try:
                index.upload_artifact(artifact, data)
            except Exception as e:  # noqa: BLE001
                self.app.display_error('failed')
                self.app.abort(f'Error uploading to repository: {index.repo} - {e}'.replace(index.auth, '*****'))
            else:
                self.app.display_success('success')

                existing_artifacts[project_name].add(artifact.name)
                project_versions[project_name][data['version']] = None

        if not options['initialize_auth']:
            if not artifacts_found:
                self.app.abort('No artifacts found')
            elif not project_versions:
                self.app.abort(code=0)

        for project_name, versions in project_versions.items():
            self.app.display_info()
            self.app.display_mini_header(project_name)
            for version in versions:
                self.app.display_info(str(index.urls.project.child(project_name, version, '').to_iri()))

        credentials.write_updated_data()


def recurse_artifacts(artifacts: list, root) -> Iterable[Path]:
    for raw_artifact in artifacts:
        artifact = Path(raw_artifact)
        if not artifact.is_absolute():
            artifact = root / artifact

        if artifact.is_file():
            yield artifact
        elif artifact.is_dir():
            yield from artifact.iterdir()


def parse_artifacts(artifact_payload):
    for match in re.finditer(r'<a [^>]+>([^<]+)</a>', artifact_payload):
        yield match.group(1)
