import json
import pathlib
import time
from contextlib import closing
from io import StringIO

import httpx

LATEST_API = 'https://api.github.com/repos/spdx/license-list-data/releases/latest'
LICENSES_URL = 'https://raw.githubusercontent.com/spdx/license-list-data/v{}/json/licenses.json'
EXCEPTIONS_URL = 'https://raw.githubusercontent.com/spdx/license-list-data/v{}/json/exceptions.json'


def download_data(url):
    for _ in range(600):
        try:
            response = httpx.get(url)
            response.raise_for_status()
        except Exception:  # noqa: BLE001
            time.sleep(1)
            continue
        else:
            return json.loads(response.content.decode('utf-8'))

    message = 'Download failed'
    raise ConnectionError(message)


def main():
    latest_version = download_data(LATEST_API)['tag_name'][1:]

    licenses = {}
    for license_data in download_data(LICENSES_URL.format(latest_version))['licenses']:
        license_id = license_data['licenseId']
        deprecated = license_data['isDeprecatedLicenseId']
        licenses[license_id.lower()] = {'id': license_id, 'deprecated': deprecated}

    exceptions = {}
    for exception_data in download_data(EXCEPTIONS_URL.format(latest_version))['exceptions']:
        exception_id = exception_data['licenseExceptionId']
        deprecated = exception_data['isDeprecatedLicenseId']
        exceptions[exception_id.lower()] = {'id': exception_id, 'deprecated': deprecated}

    project_root = pathlib.Path(__file__).resolve().parent.parent
    data_file = project_root / 'src' / 'hatchling' / 'licenses' / 'supported.py'

    with closing(StringIO()) as file_contents:
        file_contents.write(
            f"""\
from __future__ import annotations

VERSION = {latest_version!r}\n\nLICENSES: dict[str, dict[str, str | bool]] = {{
"""
        )

        for normalized_name, data in sorted(licenses.items()):
            file_contents.write(f'    {normalized_name!r}: {data!r},\n')

        file_contents.write('}\n\nEXCEPTIONS: dict[str, dict[str, str | bool]] = {\n')

        for normalized_name, data in sorted(exceptions.items()):
            file_contents.write(f'    {normalized_name!r}: {data!r},\n')

        file_contents.write('}\n')

        with data_file.open('w', encoding='utf-8') as f:
            f.write(file_contents.getvalue())


if __name__ == '__main__':
    main()
