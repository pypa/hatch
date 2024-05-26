from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

import hyperlink

if TYPE_CHECKING:
    import httpx

    from hatch.utils.fs import Path


class IndexURLs:
    def __init__(self, repo: str):
        self.repo = hyperlink.parse(repo).normalize()

        # PyPI
        if self.repo.host.endswith('pypi.org'):  # no cov
            repo_url = self.repo.replace(host='pypi.org') if self.repo.host == 'upload.pypi.org' else self.repo

            self.simple = repo_url.click('/simple/')
            self.project = repo_url.click('/project/')

        # Assume devpi
        else:
            self.simple = self.repo.child('+simple', '')
            self.project = self.repo


class PackageIndex:
    def __init__(self, repo: str, *, user='', auth='', ca_cert=None, client_cert=None, client_key=None):
        self.urls = IndexURLs(repo)
        self.repo = str(self.urls.repo)
        self.user = user
        self.auth = auth

        self.__cert = None
        if client_cert:
            self.__cert = client_cert
            if client_key:
                self.__cert = (client_cert, client_key)

        self.__verify = True
        if ca_cert:
            self.__verify = ca_cert

    @cached_property
    def client(self) -> httpx.Client:
        import httpx

        from hatch.utils.network import DEFAULT_TIMEOUT

        return httpx.Client(
            transport=httpx.HTTPTransport(retries=3, verify=self.__verify, cert=self.__cert),
            timeout=DEFAULT_TIMEOUT,
        )

    def upload_artifact(self, artifact: Path, data: dict):
        import hashlib
        import io

        data[':action'] = 'file_upload'
        data['protocol_version'] = '1'

        with artifact.open('rb') as f:
            # https://github.com/pypa/warehouse/blob/7fc3ce5bd7ecc93ef54c1652787fb5e7757fe6f2/tests/unit/packaging/test_tasks.py#L189-L191
            md5_hash = hashlib.md5()  # noqa: S324
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

            response = self.client.post(
                self.repo,
                data=data,
                files={'content': (artifact.name, f, 'application/octet-stream')},
                auth=(self.user, self.auth),
            )
            response.raise_for_status()

    def get_simple_api(self, project: str) -> httpx.Response:
        return self.client.get(
            str(self.urls.simple.child(project, '')),
            headers={'Cache-Control': 'no-cache'},
            auth=(self.user, self.auth),
        )
