from __future__ import annotations

import re
from typing import Generator

from ..utils.fs import Path
from .plugin.interface import PublisherInterface

MULTIPLE_USE_METADATA_FIELDS = {
    'classifier',
    'dynamic',
    'license_file',
    'obsoletes_dist',
    'platform',
    'project_url',
    'provides_dist',
    'provides_extra',
    'requires_dist',
    'requires_external',
    'supported_platform',
}
RENAMED_METADATA_FIELDS = {'classifier': 'classifiers', 'project_url': 'project_urls'}


class PyPIPublisher(PublisherInterface):
    PLUGIN_NAME = 'pypi'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.repos = self.plugin_config.get('repos', {}).copy()
        self.repos['main'] = 'https://upload.pypi.org/legacy/'
        self.repos['test'] = 'https://test.pypi.org/legacy/'

    def publish(self, artifacts: list, options: dict):
        """
        https://warehouse.readthedocs.io/api-reference/legacy.html#upload-api
        """
        import hashlib
        import io
        from collections import defaultdict
        from urllib.parse import urlparse

        import httpx

        if not artifacts:
            from hatchling.builders.constants import DEFAULT_BUILD_DIRECTORY

            artifacts = [DEFAULT_BUILD_DIRECTORY]

        if 'repo' in options:
            repo = options['repo']
        else:
            repo = self.plugin_config.get('repo', 'main')

        if repo in self.repos:
            repo = self.repos[repo]

        cached_user_file = CachedUserFile(self.cache_dir)
        updated_user = None
        if 'user' in options:
            user = options['user']
        else:
            user = self.plugin_config.get('user', '')
            if not user:
                user = cached_user_file.get_user(repo)
                if user is None:
                    if options['no_prompt']:
                        self.app.abort('Missing required option: user')
                    else:
                        user = updated_user = self.app.prompt('Enter your username')

        updated_auth = None
        if 'auth' in options:
            auth = options['auth']
        else:
            auth = self.plugin_config.get('auth', '')
            if not auth:
                import keyring

                auth = keyring.get_password(repo, user)
                if auth is None:
                    if options['no_prompt']:
                        self.app.abort('Missing required option: auth')
                    else:
                        auth = updated_auth = self.app.prompt('Enter your credentials', hide_input=True)

        repo_components = urlparse(repo)
        domain = repo_components.netloc
        if domain == 'upload.pypi.org':  # no cov
            domain = 'pypi.org'

        index_url = f'{repo_components.scheme}://{domain}/simple/'
        existing_artifacts: dict[str, set[str]] = {}

        # Use as an ordered set
        project_versions: dict[str, dict[str, None]] = defaultdict(dict)

        artifacts_found = False
        for artifact in recurse_artifacts(artifacts, self.root):
            if artifact.name.endswith('.whl'):
                data = get_wheel_form_data(self.app, artifact)
            elif artifact.name.endswith('.tar.gz'):
                data = get_sdist_form_data(self.app, artifact)
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
                    response = httpx.get(f'{index_url}{project_name}/')
                    response.raise_for_status()
                except Exception:  # no cov
                    existing_artifacts[project_name] = set()
                else:
                    existing_artifacts[project_name] = set(parse_artifacts(response.text))

            if artifact.name in existing_artifacts[project_name]:
                self.app.display_warning('already exists')
                continue

            data[':action'] = 'file_upload'
            data['protocol_version'] = '1'

            with artifact.open('rb') as f:
                # https://github.com/pypa/warehouse/blob/7fc3ce5bd7ecc93ef54c1652787fb5e7757fe6f2/tests/unit/packaging/test_tasks.py#L189-L191
                md5_hash = hashlib.md5()
                sha256_hash = hashlib.sha256()
                blake2_256_hash = hashlib.blake2b(digest_size=32)

                while True:
                    chunk = f.read(io.DEFAULT_BUFFER_SIZE)
                    if not chunk:
                        break

                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
                    blake2_256_hash.update(chunk)

                data['md5_digest'] = md5_hash.hexdigest()
                data['sha256_digest'] = sha256_hash.hexdigest()
                data['blake2_256_digest'] = blake2_256_hash.hexdigest()

                f.seek(0)

                try:
                    response = httpx.post(
                        repo,
                        data=data,
                        files={'content': (artifact.name, f, 'application/octet-stream')},
                        auth=(user, auth),
                    )
                    response.raise_for_status()
                except Exception as e:
                    self.app.display_error('failed')
                    self.app.abort(str(e).replace(auth, '*****'))
                else:
                    self.app.display_success('success')

                    existing_artifacts[project_name].add(artifact.name)
                    project_versions[project_name][data['version']] = None

        if not artifacts_found:
            self.app.abort('No artifacts found')
        elif not project_versions:
            self.app.abort(code=0)

        if domain.endswith('pypi.org'):
            for project_name, versions in project_versions.items():
                self.app.display_info()
                self.app.display_mini_header(project_name)
                for version in versions:
                    self.app.display_info(f'https://{domain}/project/{project_name}/{version}/')
        else:  # no cov
            for project_name in project_versions:
                self.app.display_info()
                self.app.display_mini_header(project_name)
                self.app.display_info(f'{index_url}{project_name}/')

        if updated_user is not None:
            cached_user_file.set_user(repo, user)

        if updated_auth is not None:
            import keyring

            keyring.set_password(repo, user, auth)


def get_wheel_form_data(app, artifact):
    import zipfile

    from packaging.tags import parse_tag

    with zipfile.ZipFile(str(artifact), 'r') as zip_archive:
        dist_info_dir = ''
        for path in zip_archive.namelist():
            root = path.split('/', 1)[0]
            if root.endswith('.dist-info'):
                dist_info_dir = root
                break
        else:  # no cov
            app.abort(f'Could not find the `.dist-info` directory in wheel: {artifact}')

        try:
            with zip_archive.open(f'{dist_info_dir}/METADATA') as zip_file:
                metadata_file_contents = zip_file.read().decode('utf-8')
        except KeyError:  # no cov
            app.abort(f'Could not find a `METADATA` file in the `{dist_info_dir}` directory')
        else:
            data = parse_headers(metadata_file_contents)

    data['filetype'] = 'bdist_wheel'

    # Examples:
    # cryptography-3.4.7-pp37-pypy37_pp73-manylinux2014_x86_64.whl -> pp37
    # hatchling-1rc1-py2.py3-none-any.whl -> py2.py3
    tag_component = '-'.join(artifact.stem.split('-')[-3:])
    data['pyversion'] = '.'.join(sorted(set(tag.interpreter for tag in parse_tag(tag_component))))

    return data


def get_sdist_form_data(app, artifact):
    import tarfile

    with tarfile.open(str(artifact), 'r:gz') as tar_archive:
        pkg_info_dir_parts = []
        for tar_info in tar_archive:
            if tar_info.isfile():
                pkg_info_dir_parts.extend(tar_info.name.split('/')[:-1])
                break
            else:  # no cov
                pass
        else:  # no cov
            app.abort(f'Could not find any files in sdist: {artifact}')

        pkg_info_dir_parts.append('PKG-INFO')
        pkg_info_path = '/'.join(pkg_info_dir_parts)
        try:
            with tar_archive.extractfile(pkg_info_path) as tar_file:
                metadata_file_contents = tar_file.read().decode('utf-8')
        except KeyError:  # no cov
            app.abort(f'Could not find file: {pkg_info_path}')
        else:
            data = parse_headers(metadata_file_contents)

    data['filetype'] = 'sdist'
    data['pyversion'] = 'source'

    return data


def parse_headers(metadata_file_contents):
    import email

    message = email.message_from_string(metadata_file_contents)

    headers = {'description': message.get_payload()}

    for header, value in message.items():
        normalized_header = header.lower().replace('-', '_')
        header_name = RENAMED_METADATA_FIELDS.get(normalized_header, normalized_header)

        if normalized_header in MULTIPLE_USE_METADATA_FIELDS:
            if header_name in headers:
                headers[header_name].append(value)
            else:
                headers[header_name] = [value]
        else:
            headers[header_name] = value

    return headers


def recurse_artifacts(artifacts: list, root) -> Generator[Path, None, None]:
    for artifact in artifacts:
        artifact = Path(artifact)
        if not artifact.is_absolute():
            artifact = root / artifact

        if artifact.is_file():
            yield artifact
        elif artifact.is_dir():
            yield from artifact.iterdir()


def normalize_project_name(name):
    # https://www.python.org/dev/peps/pep-0503/#normalized-names
    return re.sub(r'[-_.]+', '-', name).lower()


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
