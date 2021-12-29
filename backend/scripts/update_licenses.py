import json
import pathlib
import time
from contextlib import closing
from io import StringIO

import httpx

VERSION = '3.15'

LICENSES_URL = f'https://raw.githubusercontent.com/spdx/license-list-data/v{VERSION}/json/licenses.json'
EXCEPTIONS_URL = f'https://raw.githubusercontent.com/spdx/license-list-data/v{VERSION}/json/exceptions.json'


def download_data(url):
    for _ in range(600):
        try:
            response = httpx.get(url)
            response.raise_for_status()
        except Exception:
            time.sleep(1)
            continue
        else:
            return json.loads(response.content.decode('utf-8'))
    else:
        raise Exception('Download failed')


def main():
    licenses = {}
    for license_data in download_data(LICENSES_URL)['licenses']:
        license_id = license_data['licenseId']
        deprecated = license_data['isDeprecatedLicenseId']
        licenses[license_id.lower()] = {'id': license_id, 'deprecated': deprecated}

    exceptions = {}
    for exception_data in download_data(EXCEPTIONS_URL)['exceptions']:
        exception_id = exception_data['licenseExceptionId']
        deprecated = exception_data['isDeprecatedLicenseId']
        exceptions[exception_id.lower()] = {'id': exception_id, 'deprecated': deprecated}

    project_root = pathlib.Path(__file__).resolve().parent.parent
    data_file = project_root / 'hatchling' / 'licenses' / 'supported.py'

    with closing(StringIO()) as file_contents:
        file_contents.write(f'VERSION = {VERSION!r}\n\nLICENSES = {{\n')

        for normalized_name, data in sorted(licenses.items()):
            file_contents.write(f'    {normalized_name!r}: {data!r},\n')

        file_contents.write('}\n\nEXCEPTIONS = {\n')

        for normalized_name, data in sorted(exceptions.items()):
            file_contents.write(f'    {normalized_name!r}: {data!r},\n')

        file_contents.write('}\n')

        with data_file.open('w', encoding='utf-8') as f:
            f.write(file_contents.getvalue())


if __name__ == '__main__':
    main()
