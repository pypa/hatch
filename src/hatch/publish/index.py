from __future__ import annotations

import re
from typing import Generator

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
                data = {'url': data}
            elif not isinstance(data, dict):
                self.app.abort(f'Hatch config field `publish.index.repos.{repo}` must be a string or a mapping')
            elif 'url' not in data:
                self.app.abort(f'Hatch config field `publish.index.repos.{repo}` must define a `url` key')

            repos[repo] = data

        # Ensure PyPI correct
        for repo, url in (('main', 'https://upload.pypi.org/legacy/'), ('test', 'https://test.pypi.org/legacy/')):
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

        if not artifacts:
            from hatchling.builders.constants import DEFAULT_BUILD_DIRECTORY

            artifacts = [DEFAULT_BUILD_DIRECTORY]

        if 'repo' in options:
            repo = options['repo']
        else:
            repo = self.plugin_config.get('repo', 'main')

        repos = self.get_repos()

        if repo in repos:
            repo_config = repos[repo]
        else:
            repo_config = {'url': repo}

        index = PackageIndex(
            repo_config['url'],
            ca_cert=options.get('ca_cert', repo_config.get('ca-cert')),
            client_cert=options.get('client_cert', repo_config.get('client-cert')),
            client_key=options.get('client_key', repo_config.get('client-key')),
        )

        cached_user_file = CachedUserFile(self.cache_dir)
        updated_user = None
        if 'user' in options:
            user = options['user']
        else:
            user = repo_config.get('user', '')
            if not user:
                user = cached_user_file.get_user(repo)
                if user is None:
                    if options['no_prompt']:
                        self.app.abort('Missing required option: user')
                    else:
                        user = updated_user = self.app.prompt('Enter your username')
        index.user = user

        updated_auth = None
        if 'auth' in options:
            auth = options['auth']
        else:
            auth = repo_config.get('auth', '')
            if not auth:
                import keyring

                auth = keyring.get_password(repo, user)
                if auth is None:
                    if options['no_prompt']:
                        self.app.abort('Missing required option: auth')
                    else:
                        auth = updated_auth = self.app.prompt('Enter your credentials', hide_input=True)
        index.auth = auth

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
                except Exception:  # no cov
                    existing_artifacts[project_name] = set()
                else:
                    existing_artifacts[project_name] = set(parse_artifacts(response.text))

            if artifact.name in existing_artifacts[project_name]:
                self.app.display_warning('already exists')
                continue

            try:
                index.upload_artifact(artifact, data)
            except Exception as e:
                self.app.display_error('failed')
                self.app.abort(str(e).replace(index.auth, '*****'))
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

        if updated_user is not None:
            cached_user_file.set_user(repo, user)

        if updated_auth is not None:
            import keyring

            keyring.set_password(repo, user, auth)


def recurse_artifacts(artifacts: list, root) -> Generator[Path, None, None]:
    for artifact in artifacts:
        artifact = Path(artifact)
        if not artifact.is_absolute():
            artifact = root / artifact

        if artifact.is_file():
            yield artifact
        elif artifact.is_dir():
            yield from artifact.iterdir()


def parse_artifacts(artifact_payload):
    for match in re.finditer(r'<a [^>]+>([^<]+)</a>', artifact_payload):
        yield match.group(1)


class CachedUserFile:
    def __init__(self, cache_dir: Path):
        self.path = cache_dir / 'previous_working_users.json'

        self._data = None

    def get_user(self, repo: str):
        return self.data.get(repo)

    def set_user(self, repo: str, user: str):
        import json

        self.data[repo] = user

        self.path.ensure_parent_dir_exists()
        self.path.write_text(json.dumps(self.data))

    @property
    def data(self):
        if self._data is None:
            if not self.path.is_file():
                self._data = {}
            else:
                contents = self.path.read_text()
                if not contents:  # no cov
                    self._data = {}
                else:
                    import json

                    self._data = json.loads(contents)

        return self._data
